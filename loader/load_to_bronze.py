import argparse
import logging
import os
from datetime import date, timedelta
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

MASTER_DIR = Path("data/master")
LANDING_DIR = Path("data/landing")
STAGE = "RETAIL_DB.BRONZE.LANDING_STAGE"
FILE_FORMAT = "RETAIL_DB.BRONZE.CSV_FORMAT"


DAILY_TABLES = {
    "sales": ("RAW_SALES", ["txn_id", "line_no", "store_id", "product_id", "customer_id", "quantity",
                            "unit_price", "discount", "payment_method", "channel", "event_ts"], "append"),
    "returns": ("RAW_RETURNS", ["return_id", "txn_id", "line_no", "quantity", "refund_amount",
                                "reason_code", "return_ts"], "append"),
    "products": ("RAW_PRODUCTS", ["product_id", "product_name", "brand", "category", "sub_category",
                                  "supplier_id", "list_price", "cost", "status", "updated_at"], "replace"),
    "customers": ("RAW_CUSTOMERS", ["customer_id", "customer_name", "email", "phone", "city",
                                    "loyalty_tier", "signup_date", "updated_at"], "replace"),
}
MASTER_TABLES = {
    "stores": ("RAW_STORES", ["store_id", "store_name", "city", "region", "format", "open_date"], "replace"),
    "suppliers": ("RAW_SUPPLIERS", ["supplier_id", "supplier_name", "city"], "replace"),
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("load_to_bronze")


def get_connection():
    
    load_dotenv()
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema="BRONZE",
    )


def load_file(cur, local_path: Path, stage_folder: str, table: str, columns: list, mode: str) -> int:
   
    stage_path = f"@{STAGE}/{stage_folder}/"

    cur.execute(f"PUT 'file://{local_path.resolve().as_posix()}' {stage_path} AUTO_COMPRESS=TRUE OVERWRITE=TRUE")

    if mode == "replace":
        cur.execute(f"TRUNCATE TABLE {table}")
    else:
        cur.execute(f"DELETE FROM {table} WHERE _source_file LIKE %s", (f"%{stage_folder}/%",))
        

    positions = ", ".join(f"${i + 1}" for i in range(len(columns)))
    column_list = ", ".join(columns + ["_source_file"])
    force = "TRUE"      
    cur.execute(
        f"COPY INTO {table} ({column_list}) "
        f"FROM (SELECT {positions}, METADATA$FILENAME FROM {stage_path}) "
        f"FILE_FORMAT = (FORMAT_NAME = '{FILE_FORMAT}') FORCE = {force}"
    )
    results = cur.fetchall()
    
    return sum(int(r[3]) for r in results if len(r) > 3 and r[1] == "LOADED")


def load_master(cur) -> None:
    for name, (table, columns, mode) in MASTER_TABLES.items():
        rows = load_file(cur, MASTER_DIR / f"{name}.csv", f"master/{name}", table, columns, mode)
        log.info("%s: %d rows loaded into %s", name, rows, table)


def load_day(cur, day: date) -> None:
    for name, (table, columns, mode) in DAILY_TABLES.items():
        path = LANDING_DIR / day.isoformat() / f"{name}.csv"
        rows = load_file(cur, path, f"{name}/{day.isoformat()}", table, columns, mode)
        log.info("%s %s: %d rows loaded into %s", day, name, rows, table)


def main() -> None:
    parser = argparse.ArgumentParser(description="Load CSV files into Snowflake BRONZE")
    parser.add_argument("--master", action="store_true", help="load stores and suppliers")
    parser.add_argument("--date", help="single day, YYYY-MM-DD")
    parser.add_argument("--start", help="first day, YYYY-MM-DD")
    parser.add_argument("--end", help="last day, YYYY-MM-DD")
    args = parser.parse_args()

    conn = get_connection()
    try:
        cur = conn.cursor()
        if args.master:
            load_master(cur)
        if args.date or args.start:
            first = date.fromisoformat(args.date or args.start)
            last = date.fromisoformat(args.date or args.end or args.start)
            day = first
            while day <= last:
                load_day(cur, day)
                day += timedelta(days=1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()