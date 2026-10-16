"""
Generate a deliberately messy retail-sales dataset (10,000+ rows).

Why synthetic?  The raw file mimics what a real transaction export looks like
(mixed date formats, currency strings, typos, duplicates, missing values,
outliers) so the cleaning notebook can be demonstrated end to end and re-run.
If you have the company's own raw file, drop it in as raw_retail_sales.csv
(same column names) and the notebook will run on it unchanged.
"""
import os
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N_BASE = 10_400

# ----------------------------------------------------------------------------
# Reference tables (the "truth" the messy file is derived from)
# ----------------------------------------------------------------------------
catalog = {
    "Furniture": {
        "Chairs": ["Ergonomic Office Chair", "Executive Leather Chair", "Mesh Task Chair"],
        "Tables": ["Conference Table", "Standing Desk", "Folding Table"],
        "Bookcases": ["Oak Bookcase", "Metal Shelving Unit", "Corner Bookcase"],
        "Furnishings": ["Desk Lamp", "Wall Clock", "Floor Mat"],
    },
    "Office Supplies": {
        "Paper": ["Copy Paper Ream", "Legal Pads", "Sticky Notes Pack"],
        "Binders": ["Ring Binder 3in", "Presentation Binder", "Binder Dividers"],
        "Storage": ["File Cabinet", "Storage Box Set", "Desk Organizer"],
        "Art": ["Marker Set", "Highlighter Pack", "Pen Gift Set"],
    },
    "Technology": {
        "Phones": ["Smartphone X200", "Desk Phone Pro", "Conference Speakerphone"],
        "Accessories": ["Wireless Mouse", "USB-C Hub", "Mechanical Keyboard"],
        "Copiers": ["Laser Copier L5", "Compact Copier C2", "Color Copier CX"],
        "Machines": ["Label Printer", "Document Scanner", "Shredder Pro"],
    },
}
price_range = {"Furniture": (80, 900), "Office Supplies": (5, 120), "Technology": (20, 1800)}

products = []
pid = 1
for cat, subs in catalog.items():
    for sub, names in subs.items():
        for name in names:
            lo, hi = price_range[cat]
            products.append(
                dict(product_id=f"PRD-{pid:03d}", product_name=name, category=cat,
                     sub_category=sub, base_price=round(rng.uniform(lo, hi), 2),
                     cost_ratio=round(rng.uniform(0.55, 0.82), 3))
            )
            pid += 1
products = pd.DataFrame(products)

first = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "David", "Elizabeth",
         "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Daniel", "Karen",
         "Priya", "Arjun", "Wei", "Mei", "Carlos", "Sofia", "Omar", "Fatima", "Liam", "Emma"]
last = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
        "Hernandez", "Lopez", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee",
        "Patel", "Sharma", "Chen", "Nguyen", "Khan", "Kim", "Singh", "Reddy", "Silva", "Ali"]
region_cities = {
    "East": ["New York", "Boston", "Philadelphia", "Washington"],
    "West": ["Los Angeles", "Seattle", "San Francisco", "Denver"],
    "South": ["Houston", "Atlanta", "Miami", "Dallas"],
    "Central": ["Chicago", "Kansas City", "St. Louis", "Minneapolis"],
}
N_CUST = 2_500
cust_region = rng.choice(list(region_cities), N_CUST, p=[0.30, 0.28, 0.22, 0.20])
customers = pd.DataFrame({
    "customer_id": [f"CUST-{i:04d}" for i in range(1, N_CUST + 1)],
    "customer_name": [f"{rng.choice(first)} {rng.choice(last)}" for _ in range(N_CUST)],
    "segment": rng.choice(["Consumer", "Corporate", "Home Office"], N_CUST, p=[0.52, 0.30, 0.18]),
    "region": cust_region,
    "city": [rng.choice(region_cities[r]) for r in cust_region],
})

# ----------------------------------------------------------------------------
# Clean "truth" transactions
# ----------------------------------------------------------------------------
N = N_BASE
all_days = pd.date_range("2023-01-01", "2025-12-31")
w = np.where(np.asarray(all_days.month.isin([11, 12])), 1.7, 1.0)
w = w * (1 + 0.15 * (np.asarray(all_days.year) - 2023))          # mild growth
order_dates = rng.choice(all_days, N, p=w / w.sum())

ship_modes = rng.choice(["Standard Class", "Second Class", "First Class", "Same Day"], N, p=[0.60, 0.20, 0.15, 0.05])
lead = {"Standard Class": (5, 8), "Second Class": (3, 5), "First Class": (1, 3), "Same Day": (0, 0)}
lead_days = np.array([rng.integers(lead[m][0], lead[m][1] + 1) for m in ship_modes])
ship_dates = pd.DatetimeIndex(order_dates) + pd.to_timedelta(lead_days, unit="D")

cust = customers.iloc[rng.integers(0, N_CUST, N)].reset_index(drop=True)
prod = products.iloc[rng.choice(len(products), N)].reset_index(drop=True)

qty = rng.choice(np.arange(1, 11), N, p=[0.22, 0.20, 0.16, 0.12, 0.10, 0.07, 0.05, 0.04, 0.02, 0.02])
unit_price = np.round(prod["base_price"].values * rng.uniform(0.97, 1.03, N), 2)
discount = rng.choice([0, 0.05, 0.10, 0.15, 0.20, 0.30], N, p=[0.45, 0.10, 0.20, 0.10, 0.10, 0.05])
sales = np.round(qty * unit_price * (1 - discount), 2)
cost = np.round(qty * unit_price * prod["cost_ratio"].values, 2)
profit = np.round(sales - cost, 2)
pay = rng.choice(["Credit Card", "Debit Card", "Cash", "UPI", "PayPal"], N, p=[0.38, 0.25, 0.12, 0.15, 0.10])

df = pd.DataFrame({
    "order_id": [f"ORD-{100000 + i}" for i in range(N)],
    "order_date": pd.DatetimeIndex(order_dates),
    "ship_date": ship_dates,
    "ship_mode": ship_modes,
    "customer_id": cust["customer_id"],
    "customer_name": cust["customer_name"],
    "segment": cust["segment"],
    "region": cust["region"],
    "city": cust["city"],
    "product_id": prod["product_id"],
    "product_name": prod["product_name"],
    "category": prod["category"],
    "sub_category": prod["sub_category"],
    "quantity": qty,
    "unit_price": unit_price,
    "discount": discount,
    "sales": sales,
    "cost": cost,
    "profit": profit,
    "payment_method": pay,
})


def pick(p):
    return rng.random(len(df)) < p


NULL_TOKENS = [np.nan, np.nan, np.nan, "", "N/A", "n/a", "NULL", "?", "-", "unknown"]


def null_token(n):
    return [NULL_TOKENS[i] for i in rng.integers(0, len(NULL_TOKENS), n)]


# ----------------------------------------------------------------------------
# 1. Dates -> inconsistent string formats, invalid and missing values
# ----------------------------------------------------------------------------
fmts = ["%Y-%m-%d", "%d/%m/%Y", "%b %d, %Y", "%d-%b-%Y"]
fmt_choice = rng.choice(len(fmts), len(df), p=[0.40, 0.25, 0.20, 0.15])


def fmt_dates(series, choice):
    return pd.Series([d.strftime(fmts[c]) if pd.notna(d) else np.nan for d, c in zip(series, choice)], dtype=object)


# a few ship dates that fall BEFORE the order date (data-entry errors)
bad_ship = pick(0.015)
df.loc[bad_ship, "ship_date"] = df.loc[bad_ship, "order_date"] - pd.to_timedelta(rng.integers(1, 10, bad_ship.sum()), unit="D")

raw = df.copy()
raw["order_date"] = fmt_dates(df["order_date"], fmt_choice)
raw["ship_date"] = fmt_dates(df["ship_date"], rng.choice(len(fmts), len(df), p=[0.55, 0.20, 0.15, 0.10]))

m = pick(0.012)  # missing order dates
raw.loc[m, "order_date"] = null_token(m.sum())
m = pick(0.004)  # impossible dates
raw.loc[m, "order_date"] = rng.choice(["31/02/2024", "2024-13-05", "00/00/0000", "2099-01-15"], m.sum())
m = pick(0.025)  # missing ship dates
raw.loc[m, "ship_date"] = null_token(m.sum())

# ----------------------------------------------------------------------------
# 2. Categorical text: casing, whitespace, abbreviations, typos, missing
# ----------------------------------------------------------------------------
def scramble(series, variants, p):
    out = series.astype(object).copy()
    m = pick(p)
    out[m] = [variants[v][rng.integers(0, len(variants[v]))] if v in variants else v for v in series[m]]
    return out


raw["region"] = scramble(df["region"], {
    "East": ["east", "EAST", "East ", "E", "Eest"], "West": ["west", "WEST", " West", "W", "Wset"],
    "South": ["south", "SOUTH", "South ", "S", "Sout"], "Central": ["central", "CENTRAL", "Central ", "C", "Centrl"],
}, 0.22)
raw["category"] = scramble(df["category"], {
    "Furniture": ["furniture", "FURNITURE", " Furniture", "Furnitur"],
    "Office Supplies": ["office supplies", "OFFICE SUPPLIES", "Office Supply", "Office  Supplies"],
    "Technology": ["technology", "TECHNOLOGY", "Tech", "Technolgy "],
}, 0.18)
raw["segment"] = scramble(df["segment"], {
    "Consumer": ["consumer", "CONSUMER", "Consumer "], "Corporate": ["corporate", "CORPORATE", "Corp"],
    "Home Office": ["home office", "HOME OFFICE", "Home-Office", "HomeOffice"],
}, 0.15)
raw["ship_mode"] = scramble(df["ship_mode"], {
    "Standard Class": ["standard class", "Standard", "STANDARD CLASS"], "Second Class": ["second class", "Second", "2nd Class"],
    "First Class": ["first class", "First", "1st Class"], "Same Day": ["same day", "SAME DAY", "Same-Day"],
}, 0.20)
raw["payment_method"] = scramble(df["payment_method"], {
    "Credit Card": ["credit card", "CC", "Credit card", "CREDIT CARD"], "Debit Card": ["debit card", "DC", "Debit card"],
    "Cash": ["cash", "CASH", "Cash "], "UPI": ["upi", "Upi"], "PayPal": ["paypal", "Paypal", "PAYPAL"],
}, 0.20)

# stray whitespace / casing in free-text columns
m = pick(0.05)
raw.loc[m, "customer_name"] = raw.loc[m, "customer_name"].map(lambda s: f"  {s.upper()} ")
m = pick(0.04)
raw.loc[m, "product_name"] = raw.loc[m, "product_name"].str.lower()
m = pick(0.03)
raw.loc[m, "city"] = raw.loc[m, "city"].str.upper() + " "

# missing values in categoricals / identifiers
for col, p in [("customer_name", 0.03), ("region", 0.035), ("category", 0.025), ("segment", 0.02),
               ("ship_mode", 0.03), ("city", 0.03), ("payment_method", 0.02), ("sub_category", 0.02),
               ("product_name", 0.015)]:
    m = pick(p)
    raw.loc[m, col] = null_token(m.sum())

# ----------------------------------------------------------------------------
# 3. Numerics -> strings with symbols, wrong scales, outliers, negatives, NaNs
# ----------------------------------------------------------------------------
qty_raw = df["quantity"].astype(object).copy()
NUM_WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}
m = pick(0.006)
qty_raw[m] = [NUM_WORDS[q] for q in df.loc[m, "quantity"]]     # spelled-out numbers ("three")
m = pick(0.006)
qty_raw[m] = [f"{q} units" for q in df.loc[m, "quantity"]]
m = pick(0.004)
qty_raw[m] = -df.loc[m, "quantity"]                          # sign errors
m = pick(0.004)
qty_raw[m] = rng.choice([500, 750, 999, 1200], m.sum())      # extreme outliers
m = pick(0.03)
qty_raw[m] = null_token(m.sum())
raw["quantity"] = qty_raw

price_raw = df["unit_price"].astype(object).copy()
m = pick(0.004)
price_raw[m] = df.loc[m, "unit_price"] * rng.choice([10, 100], m.sum())   # extra zero typos
fm = pick(0.30)
price_raw[fm] = [f"${float(v):,.2f}" for v in price_raw[fm]]
fm = pick(0.03)
price_raw[fm] = [f"USD {float(v):.2f}" if not isinstance(v, str) else v for v in price_raw[fm]]
m = pick(0.035)
price_raw[m] = null_token(m.sum())
raw["unit_price"] = price_raw

disc_raw = df["discount"].astype(object).copy()
m = pick(0.40)
disc_raw[m] = [f"{int(round(v * 100))}%" for v in df.loc[m, "discount"]]
m = pick(0.15)
disc_raw[m] = [f"{v:.2f}" for v in df.loc[m, "discount"]]
m = pick(0.08)
disc_raw[m] = [int(round(v * 100)) for v in df.loc[m, "discount"]]       # 10 instead of 0.10
m = pick(0.03)
disc_raw[m] = null_token(m.sum())
raw["discount"] = disc_raw

sales_raw = df["sales"].astype(object).copy()
fm = pick(0.35)
sales_raw[fm] = [f"${v:,.2f}" for v in df.loc[fm, "sales"]]
m = pick(0.03)
sales_raw[m] = null_token(m.sum())
raw["sales"] = sales_raw

cost_raw = df["cost"].astype(object).copy()
fm = pick(0.20)
cost_raw[fm] = [f"${v:,.2f}" for v in df.loc[fm, "cost"]]
m = pick(0.045)
cost_raw[m] = null_token(m.sum())
raw["cost"] = cost_raw

profit_raw = df["profit"].astype(object).copy()
fm = pick(0.20)
profit_raw[fm] = [f"${v:,.2f}" if v >= 0 else f"(${abs(v):,.2f})" for v in df.loc[fm, "profit"]]  # accounting negatives
m = pick(0.03)
profit_raw[m] = null_token(m.sum())
raw["profit"] = profit_raw

# ----------------------------------------------------------------------------
# 4. Duplicates: exact copies + near-duplicates (same order_id, messy text)
# ----------------------------------------------------------------------------
exact = raw.sample(300, random_state=1)
near = raw.sample(120, random_state=2).copy()
near["customer_name"] = near["customer_name"].astype(str).str.upper()
near["region"] = near["region"].astype(str) + " "
near["category"] = near["category"].astype(str).str.lower()

raw = pd.concat([raw, exact, near], ignore_index=True).sample(frac=1, random_state=7).reset_index(drop=True)

out_dir = Path("data") if Path("data").exists() else Path(".")
out_file = out_dir / "raw_retail_sales.csv"
raw.to_csv(out_file, index=False)
print(f"{out_file} ->", raw.shape)
