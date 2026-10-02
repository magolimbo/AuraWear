"""Generate synthetic daily source files (see data_gen/SPEC.md)."""

import argparse
import csv
import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from data_gen.templates import CHAT_OPENINGS, FOLLOW_UP_TURNS, RATING_COMMENTS

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


def choose_label(order: dict[str, str], is_chat: bool, rng: random.Random) -> tuple[str, str]:
    """Return (category, sentiment) for a rating or chat, following the table in SPEC.md §3."""
    if order["product_id"] == "P03":
        return "fit_sizing", "negative"
    if order["product_id"] == "P07":
        return "product_quality", "negative"
    if order["returned"] == "true":
        return rng.choice(["fit_sizing", "product_quality", "returns_refunds"]), "negative"
    if is_chat:
        return rng.choice(["fit_sizing", "product_quality"]), "negative"
    sentiment = "positive" if rng.random() < 0.8 else "neutral"
    return rng.choice(["fit_sizing", "product_quality", "other"]), sentiment


def random_timestamp(day: date, rng: random.Random) -> str:
    """Return an ISO 8601 UTC timestamp at a random time of the given day."""
    moment = datetime(day.year, day.month, day.day) + timedelta(seconds=rng.randrange(86400))
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def make_rating(order: dict[str, str], rng: random.Random) -> dict[str, str]:
    """Return a rating for the order, with a comment half of the time."""
    category, sentiment = choose_label(order, is_chat=False, rng=rng)
    stars = {"negative": rng.randint(1, 2), "neutral": 3, "positive": rng.randint(4, 5)}[sentiment]
    rating = {
        "review_id": f"R{order['order_id']}",
        "order_id": order["order_id"],
        "product_id": order["product_id"],
        "stars": str(stars),
    }
    if rng.random() < 0.5:
        template = rng.choice(RATING_COMMENTS[(category, sentiment)])
        rating["comment"] = template.format(product=order["product_name"])
    rating["created_at"] = random_timestamp(date.fromisoformat(order["order_date"]), rng)
    return rating


def make_chat(order: dict[str, str], rng: random.Random) -> dict[str, str]:
    """Return a support chat about the order: a complaint, then 3-5 follow-up turns."""
    category, _ = choose_label(order, is_chat=True, rng=rng)
    opening = f"Customer: {rng.choice(CHAT_OPENINGS[category])}"
    turns = [opening] + FOLLOW_UP_TURNS[: rng.randint(3, 5)]
    return {
        "chat_id": f"CH{order['order_id']}",
        "order_id": order["order_id"],
        "transcript": "\n".join(turns).format(product=order["product_name"]),
        "started_at": random_timestamp(date.fromisoformat(order["order_date"]), rng),
    }


def make_feedback(
    orders: list[dict[str, str]], rng: random.Random
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return (ratings, chats) for the orders of one day."""
    ratings, chats = [], []
    for order in orders:
        if rng.random() < 0.8:
            ratings.append(make_rating(order, rng))
        chat_rate = 0.5 if order["returned"] == "true" else 0.1
        if rng.random() < chat_rate:
            chats.append(make_chat(order, rng))
    return ratings, chats


def add_dirty_rows(
    ratings: list[dict[str, str]], chats: list[dict[str, str]], rng: random.Random
) -> None:
    """Make about 2% of feedback rows dirty, in place: out-of-range stars and duplicates."""
    dirty = max(2, round(0.02 * (len(ratings) + len(chats))))
    for rating in rng.sample(ratings, dirty // 2):
        rating["stars"] = rng.choice(["0", "6"])
    for row in rng.sample(ratings + chats, dirty - dirty // 2):
        (ratings if "review_id" in row else chats).append(dict(row))


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    """Write rows as CSV with a header, creating the folder if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json_lines(path: Path, rows: list[dict[str, str]]) -> None:
    """Write rows as newline-delimited JSON, creating the folder if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def generate(days: int, orders_per_day: int, start_date: date, seed: int) -> None:
    """Write the source files for each day into OUT_DIR."""
    rng = random.Random(seed)
    for offset in range(days):
        day = start_date + timedelta(days=offset)
        orders = make_orders(day, orders_per_day, rng)
        ratings, chats = make_feedback(orders, rng)
        add_dirty_rows(ratings, chats, rng)
        write_csv(OUT_DIR / "orders" / f"{day}.csv", orders, ORDER_COLUMNS)
        write_json_lines(OUT_DIR / "web_rating" / f"{day}.json", ratings)
        write_json_lines(OUT_DIR / "support_chat" / f"{day}.json", chats)


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
