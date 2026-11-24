import logging
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
from faker import Faker

SEED = 42
OUTPUT_DIR = Path("data/master")
SIM_START = date(2026, 8, 1)  
N_SUPPLIERS = 40
N_PRODUCTS = 800
N_CUSTOMERS = 5000

random.seed(SEED)
Faker.seed(SEED)
fake = Faker()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("master_data")

STORES = [
    ("S01", "Mart Koteshwor", "Kathmandu", "Bagmati", "HYPERMARKET", date(2018, 3, 1)),
    ("S02", "Mart Baneshwor", "Kathmandu", "Bagmati", "SUPERMARKET", date(2019, 6, 15)),
    ("S03", "Mart Jawalakhel", "Lalitpur", "Bagmati", "SUPERMARKET", date(2020, 1, 10)),
    ("S04", "Mart Lakeside", "Pokhara", "Gandaki", "HYPERMARKET", date(2021, 9, 5)),
    ("S05", "Mart Biratnagar", "Biratnagar", "Koshi", "SUPERMARKET", date(2022, 11, 20)),
]


CATALOG = {
    "Grocery": (["Rice & Grains", "Pulses", "Oil & Ghee", "Spices", "Flour"], (60, 1500), (0.08, 0.18)),
    "Dairy": (["Milk", "Curd", "Cheese", "Butter"], (40, 900), (0.10, 0.20)),
    "Beverages": (["Tea", "Coffee", "Juice", "Soft Drinks"], (30, 800), (0.15, 0.30)),
    "Snacks": (["Noodles", "Biscuits", "Chips", "Chocolates"], (20, 600), (0.15, 0.30)),
    "Fresh Produce": (["Vegetables", "Fruits"], (30, 500), (0.10, 0.25)),
    "Household": (["Cleaning", "Kitchenware", "Laundry"], (50, 3000), (0.15, 0.35)),
    "Personal Care": (["Soap", "Shampoo", "Skin Care", "Oral Care"], (40, 2500), (0.20, 0.40)),
    "Electronics": (["Small Appliances", "Accessories"], (500, 25000), (0.08, 0.20)),
    "Clothing": (["Menswear", "Womenswear", "Kidswear"], (300, 6000), (0.25, 0.45)),
}
BRANDS = ["Himal Harvest", "Kanchan Foods", "Koshi Fresh", "Lumbini Select", "Terai Gold",
          "Gandaki Pure", "Mustang Choice", "Kathmandu Basics", "Pokhara Home", "Nepal Value"]
CITIES = ["Kathmandu", "Lalitpur", "Bhaktapur", "Pokhara", "Biratnagar", "Butwal"]
TIERS = ["BRONZE", "SILVER", "GOLD", "PLATINUM"]
TIER_WEIGHTS = [0.55, 0.28, 0.14, 0.03]


def build_stores() -> pd.DataFrame:
    return pd.DataFrame(
        STORES, columns=["store_id", "store_name", "city", "region", "format", "open_date"]
    )


def build_suppliers() -> pd.DataFrame:
    rows = [(f"SUP{i:03d}", fake.company(), random.choice(CITIES)) for i in range(1, N_SUPPLIERS + 1)]
    return pd.DataFrame(rows, columns=["supplier_id", "supplier_name", "city"])


def build_products(suppliers: pd.DataFrame) -> pd.DataFrame:
    supplier_ids = suppliers["supplier_id"].tolist()
    categories = list(CATALOG)
    rows = []
    for i in range(1, N_PRODUCTS + 1):
        category = random.choice(categories)
        subs, (pmin, pmax), (mmin, mmax) = CATALOG[category]
        sub_category = random.choice(subs)
        brand = random.choice(BRANDS)
        list_price = round(random.uniform(pmin, pmax) / 5) * 5  # prices in multiples of 5
        cost = round(list_price * (1 - random.uniform(mmin, mmax)), 2)
        rows.append((
            f"P{i:04d}", f"{brand} {sub_category}", brand, category, sub_category,
            random.choice(supplier_ids), list_price, cost, "ACTIVE", SIM_START.isoformat(),
        ))
    return pd.DataFrame(rows, columns=[
        "product_id", "product_name", "brand", "category", "sub_category",
        "supplier_id", "list_price", "cost", "status", "updated_at",
    ])


def build_customers() -> pd.DataFrame:
    rows = []
    for i in range(1, N_CUSTOMERS + 1):
        phone = f"98{random.randint(10000000, 99999999)}"
        email = fake.email()
       
        if random.random() < 0.05:
            phone = f"+977-{phone}"
        if random.random() < 0.03:
            email = email.upper()
        signup = fake.date_between(start_date=date(2022, 1, 1), end_date=SIM_START - timedelta(days=1))
        rows.append((
            f"C{i:05d}", fake.name(), email, phone, random.choice(CITIES),
            random.choices(TIERS, TIER_WEIGHTS)[0], signup.isoformat(), SIM_START.isoformat(),
        ))
    return pd.DataFrame(rows, columns=[
        "customer_id", "customer_name", "email", "phone", "city",
        "loyalty_tier", "signup_date", "updated_at",
    ])


def write_csv(df: pd.DataFrame, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{name}.csv"
    df.to_csv(path, index=False)
    log.info("Wrote %s (%d rows)", path, len(df))


def main() -> None:
    suppliers = build_suppliers()
    write_csv(build_stores(), "stores")
    write_csv(suppliers, "suppliers")
    write_csv(build_products(suppliers), "products")
    write_csv(build_customers(), "customers")


if __name__ == "__main__":
    main()