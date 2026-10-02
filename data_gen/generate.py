"""Generate synthetic daily source files (see data_gen/SPEC.md)."""

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

OUT_DIR = Path("data")

PRODUCTS = {
    "P01": "Linen Shirt",
    "P02": "Slim Chinos",
    "P03": "Denim Jacket",
    "P04": "Cotton T-Shirt",
    "P05": "Midi Dress",
    "P06": "Hooded Sweatshirt",
    "P07": "Wool Sweater",
    "P08": "Leather Belt",
    "P09": "Pleated Skirt",
    "P10": "Puffer Vest",
    "P11": "Silk Blouse",
    "P12": "Cargo Trousers",
}
PROBLEM_PRODUCTS = {"P03", "P07"}
CUSTOMERS = [f"C{i:04d}" for i in range(1, 301)]

ORDER_COLUMNS = ["order_id", "order_date", "customer_id", "product_id", "product_name", "returned"]


def make_orders(day: date, count: int, rng: random.Random) -> list[dict[str, str]]:
    """Return the orders of one day."""
    orders = []
    for number in range(1, count + 1):
        product_id = rng.choice(list(PRODUCTS))
        return_rate = 0.35 if product_id in PROBLEM_PRODUCTS else 0.10
        orders.append(
            {
                "order_id": f"O{day:%Y%m%d}-{number:04d}",
                "order_date": day.isoformat(),
                "customer_id": rng.choice(CUSTOMERS),
                "product_id": product_id,
                "product_name": PRODUCTS[product_id],
                "returned": "true" if rng.random() < return_rate else "false",
            }
        )
    return orders


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    """Write rows as CSV with a header, creating the folder if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def generate(days: int, orders_per_day: int, start_date: date, seed: int) -> None:
    """Write the source files for each day into OUT_DIR."""
    rng = random.Random(seed)
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        orders = make_orders(day, orders_per_day, rng)
        write_csv(OUT_DIR / "orders" / f"{day}.csv", orders, ORDER_COLUMNS)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=3)
    parser.add_argument("--orders-per-day", type=int, default=200)
    parser.add_argument("--start-date", type=date.fromisoformat, default=date(2026, 9, 1))
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    generate(args.days, args.orders_per_day, args.start_date, args.seed)


if __name__ == "__main__":
    main()
