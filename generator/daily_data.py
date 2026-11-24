import argparse
import logging
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
MASTER_DIR = Path("data/master")
LANDING_DIR = Path("data/landing")

HISTORY_START = date(2026, 10, 1)      
DEFAULT_END = date(2026, 11, 23)       
EVENT_WINDOW_DAYS = 90                 
BASE_INVOICES_PER_DAY = 1200

STORE_WEIGHT = {"S01": 0.30, "S02": 0.25, "S03": 0.18, "S04": 0.15, "S05": 0.12}
PAYMENT_WEIGHT = {"CASH": 0.35, "CARD": 0.20, "ESEWA": 0.20, "KHALTI": 0.10, "FONEPAY": 0.15}
CATEGORY_WEIGHT = {
    "Grocery": 0.26, "Dairy": 0.12, "Beverages": 0.10, "Snacks": 0.14, "Fresh Produce": 0.12,
    "Household": 0.08, "Personal Care": 0.08, "Electronics": 0.03, "Clothing": 0.07,
}
WEEKDAY_FACTOR = {4: 1.15, 5: 1.30}    
RETURN_REASONS = {"CHANGED_MIND": 0.35, "DAMAGED": 0.25, "EXPIRED": 0.15, "WRONG_ITEM": 0.15, "QUALITY": 0.10}
TIER_ORDER = ["BRONZE", "SILVER", "GOLD", "PLATINUM"]

SALES_COLUMNS = [
    "txn_id", "line_no", "store_id", "product_id", "customer_id", "quantity",
    "unit_price", "discount", "payment_method", "channel", "event_ts",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("daily_data")


def daily_rng(day: date, salt: int = 0) -> np.random.Generator:
    
    return np.random.default_rng(SEED * 1000 + day.toordinal() + salt)




def build_price_events(products: pd.DataFrame) -> pd.DataFrame:
    
    rng = np.random.default_rng(SEED)
    base_price = products.set_index("product_id")["list_price"]
    events = []
    for product_id in products["product_id"]:
        if rng.random() >= 0.30:           
            continue
        price = int(base_price[product_id])
        offsets = np.sort(rng.integers(0, EVENT_WINDOW_DAYS, size=rng.integers(1, 3)))
        for offset in offsets:
            price = max(5, int(round(price * rng.uniform(0.92, 1.12) / 5) * 5))
            events.append((product_id, HISTORY_START + timedelta(days=int(offset)), price))
    return pd.DataFrame(events, columns=["product_id", "change_date", "new_price"])


def build_tier_events(customers: pd.DataFrame) -> pd.DataFrame:
    
    rng = np.random.default_rng(SEED + 1)
    events = []
    for customer_id, tier in zip(customers["customer_id"], customers["loyalty_tier"]):
        position = TIER_ORDER.index(tier)
        if position < len(TIER_ORDER) - 1 and rng.random() < 0.20:  
            change_date = HISTORY_START + timedelta(days=int(rng.integers(0, EVENT_WINDOW_DAYS)))
            events.append((customer_id, change_date, TIER_ORDER[position + 1]))
    return pd.DataFrame(events, columns=["customer_id", "change_date", "new_tier"])


def latest_events(events: pd.DataFrame, day: date) -> pd.DataFrame:
    
    past = events[events["change_date"] <= day]
    return past.sort_values("change_date").groupby(past.columns[0]).tail(1)


def products_on(day: date, products: pd.DataFrame, price_events: pd.DataFrame) -> pd.DataFrame:
    snapshot = products.copy()
    latest = latest_events(price_events, day)
    if latest.empty:
        return snapshot
    snapshot = snapshot.merge(latest, on="product_id", how="left")
    changed = snapshot["new_price"].notna()
    ratio = snapshot.loc[changed, "new_price"] / snapshot.loc[changed, "list_price"]
    snapshot.loc[changed, "cost"] = (snapshot.loc[changed, "cost"] * ratio).round(2)
    snapshot.loc[changed, "list_price"] = snapshot.loc[changed, "new_price"]
    snapshot.loc[changed, "updated_at"] = snapshot.loc[changed, "change_date"].astype(str)
    snapshot["list_price"] = snapshot["list_price"].astype(int)
    return snapshot.drop(columns=["change_date", "new_price"])


def customers_on(day: date, customers: pd.DataFrame, tier_events: pd.DataFrame) -> pd.DataFrame:
    snapshot = customers.copy()
    latest = latest_events(tier_events, day)
    if latest.empty:
        return snapshot
    snapshot = snapshot.merge(latest, on="customer_id", how="left")
    changed = snapshot["new_tier"].notna()
    snapshot.loc[changed, "loyalty_tier"] = snapshot.loc[changed, "new_tier"]
    snapshot.loc[changed, "updated_at"] = snapshot.loc[changed, "change_date"].astype(str)
    return snapshot.drop(columns=["change_date", "new_tier"])




def build_clean_sales(day: date, ctx: dict) -> pd.DataFrame:
    
    rng = daily_rng(day)
    products = products_on(day, ctx["products"], ctx["price_events"])
    multiplier = ctx["multipliers"].get(day, 1.0)

    n_invoices = int(BASE_INVOICES_PER_DAY * WEEKDAY_FACTOR.get(day.weekday(), 1.0)
                     * multiplier * rng.uniform(0.9, 1.1))

    
    inv_store = rng.choice(list(STORE_WEIGHT), size=n_invoices, p=list(STORE_WEIGHT.values()))
    inv_payment = rng.choice(list(PAYMENT_WEIGHT), size=n_invoices, p=list(PAYMENT_WEIGHT.values()))
    inv_channel = np.where(rng.random(n_invoices) < 0.10, "APP", "IN_STORE")
    inv_customer = np.where(rng.random(n_invoices) < 0.60,
                            rng.choice(ctx["customer_ids"], size=n_invoices), None)
    inv_seconds = rng.integers(8 * 3600, 21 * 3600, size=n_invoices)    
    inv_txn = np.array([f"{store}-{day:%Y%m%d}-{i + 1:05d}" for i, store in enumerate(inv_store)])
    lines_per_invoice = rng.choice([1, 2, 3, 4, 5, 6], size=n_invoices,
                                   p=[0.25, 0.28, 0.22, 0.13, 0.08, 0.04])

    
    inv_idx = np.repeat(np.arange(n_invoices), lines_per_invoice)
    n = len(inv_idx)
    line_no = pd.Series(inv_idx).groupby(inv_idx).cumcount().to_numpy() + 1

    
    category_size = products["category"].map(products["category"].value_counts())
    weights = products["category"].map(CATEGORY_WEIGHT) / category_size
    weights = (weights / weights.sum()).to_numpy()
    chosen = products.iloc[rng.choice(len(products), size=n, p=weights)].reset_index(drop=True)

    quantity = rng.choice([1, 2, 3, 4, 5], size=n, p=[0.55, 0.20, 0.12, 0.08, 0.05])
    quantity = np.where(chosen["category"] == "Electronics", 1, quantity)
    unit_price = chosen["list_price"].to_numpy()
    gross = quantity * unit_price
    discount_chance = 0.35 if multiplier > 1.3 else 0.15              
    discount = np.where(rng.random(n) < discount_chance,
                        np.round(gross * rng.choice([0.05, 0.10, 0.15, 0.20], size=n), 2), 0.0)
    return_delay = np.where(rng.random(n) < 0.015, rng.integers(1, 4, size=n), 0)   

    return pd.DataFrame({
        "txn_id": inv_txn[inv_idx],
        "line_no": line_no,
        "store_id": inv_store[inv_idx],
        "product_id": chosen["product_id"],
        "customer_id": inv_customer[inv_idx],
        "quantity": quantity,
        "unit_price": unit_price,
        "discount": discount,
        "payment_method": inv_payment[inv_idx],
        "channel": inv_channel[inv_idx],
        "event_ts": pd.Timestamp(day) + pd.to_timedelta(inv_seconds[inv_idx], unit="s"),
        "category": chosen["category"],
        "return_delay": return_delay,
    })


def add_dirty_data(df: pd.DataFrame, day: date) -> pd.DataFrame:
    
    rng = daily_rng(day, salt=1)
    df = df.copy()
    n = len(df)

    late = rng.random(n) < 0.02                       
    df.loc[late, "event_ts"] -= pd.Timedelta(days=1)

    bad_qty = rng.random(n) < 0.005                  
    df.loc[bad_qty, "quantity"] = rng.choice([0, -1], size=int(bad_qty.sum()))

    no_store = rng.random(n) < 0.005                  
    df.loc[no_store, "store_id"] = None

    duplicates = df.sample(frac=0.01, random_state=int(rng.integers(0, 1_000_000)))   
    return pd.concat([df, duplicates], ignore_index=True)




def build_returns(day: date, ctx: dict) -> pd.DataFrame:
    
    parts = []
    for k in (1, 2, 3):
        sale_day = day - timedelta(days=k)
        if sale_day < HISTORY_START:
            continue
        sold = build_clean_sales(sale_day, ctx)
        parts.append(sold[sold["return_delay"] == k])
    columns = ["return_id", "txn_id", "line_no", "quantity", "refund_amount", "reason_code", "return_ts"]
    if not parts:
        return pd.DataFrame(columns=columns)

    lines = pd.concat(parts, ignore_index=True)
    rng = daily_rng(day, salt=2)
    n = len(lines)
    qty_back = np.array([rng.integers(1, int(q) + 1) for q in lines["quantity"]])
    net_amount = lines["quantity"] * lines["unit_price"] - lines["discount"]
    returns = pd.DataFrame({
        "return_id": [f"R{day:%Y%m%d}-{i + 1:05d}" for i in range(n)],
        "txn_id": lines["txn_id"],
        "line_no": lines["line_no"],
        "quantity": qty_back,
        "refund_amount": np.round(net_amount * qty_back / lines["quantity"], 2),
        "reason_code": rng.choice(list(RETURN_REASONS), size=n, p=list(RETURN_REASONS.values())),
        "return_ts": lines["event_ts"] + pd.to_timedelta(lines["return_delay"], unit="D")
                     + pd.to_timedelta(rng.integers(1, 8, size=n), unit="h"),
    })
    unknown = rng.random(n) < 0.03                    
    returns.loc[unknown, "txn_id"] = "UNKNOWN"
    return returns




def load_context() -> dict:
    products = pd.read_csv(MASTER_DIR / "products.csv")
    customers = pd.read_csv(MASTER_DIR / "customers.csv")
    calendar_path = MASTER_DIR / "festival_calendar.csv"
    multipliers = {}
    if calendar_path.exists():
        calendar = pd.read_csv(calendar_path, parse_dates=["date"])
        multipliers = {d.date(): m for d, m in zip(calendar["date"], calendar["sales_multiplier"])}
    else:
        log.warning("festival_calendar.csv not found, using normal sales every day")
    return {
        "products": products,
        "customers": customers,
        "customer_ids": customers["customer_id"].to_numpy(),
        "price_events": build_price_events(products),
        "tier_events": build_tier_events(customers),
        "multipliers": multipliers,
    }


def write_day(day: date, ctx: dict) -> None:
    out_dir = LANDING_DIR / day.isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)

    sales = add_dirty_data(build_clean_sales(day, ctx)[SALES_COLUMNS], day)
    returns = build_returns(day, ctx)

    sales.to_csv(out_dir / "sales.csv", index=False)
    returns.to_csv(out_dir / "returns.csv", index=False)
    products_on(day, ctx["products"], ctx["price_events"]).to_csv(out_dir / "products.csv", index=False)
    customers_on(day, ctx["customers"], ctx["tier_events"]).to_csv(out_dir / "customers.csv", index=False)
    log.info("%s: %d sales rows, %d returns", day, len(sales), len(returns))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate daily retail data")
    parser.add_argument("--date", help="single day, YYYY-MM-DD")
    parser.add_argument("--start", default=HISTORY_START.isoformat())
    parser.add_argument("--end", default=DEFAULT_END.isoformat())
    args = parser.parse_args()

    first = date.fromisoformat(args.date or args.start)
    last = date.fromisoformat(args.date or args.end)
    ctx = load_context()
    day = first
    while day <= last:
        write_day(day, ctx)
        day += timedelta(days=1)


if __name__ == "__main__":
    main()