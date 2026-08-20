import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from pymongo import ASCENDING, DESCENDING, TEXT


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.database import (  # noqa: E402
    close_database,
    connect_to_database,
    get_database,
)


SAMPLE_DATA = PROJECT_ROOT / "sample_data"


def load_json(filename: str) -> list[dict]:
    with (SAMPLE_DATA / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


def parse_datetime(value):
    if value is None or isinstance(value, datetime):
        return value

    return datetime.fromisoformat(value)


def prepare_order(document: dict) -> dict:
    prepared = dict(document)

    for field in ("order_date", "estimated_delivery", "delivered_at"):
        prepared[field] = parse_datetime(prepared.get(field))

    return prepared


def prepare_faq(document: dict) -> dict:
    prepared = dict(document)
    prepared["updated_at"] = parse_datetime(prepared.get("updated_at"))
    return prepared


async def ensure_indexes(database) -> None:
    await database.orders.create_index("order_id", unique=True)
    await database.orders.create_index("customer_id")

    await database.faqs.create_index("faq_id", unique=True)
    await database.faqs.create_index(
        [
            ("question", TEXT),
            ("answer", TEXT),
            ("keywords", TEXT),
        ],
        name="faq_text_search",
    )

    await database.tickets.create_index("ticket_id", unique=True)
    await database.tickets.create_index(
        [("customer_id", ASCENDING), ("created_at", DESCENDING)]
    )
    await database.tickets.create_index(
        [("status", ASCENDING), ("created_at", DESCENDING)]
    )
    await database.tickets.create_index("analysis.category")

    await database.ai_usage_logs.create_index("created_at")
    await database.ai_usage_logs.create_index("ticket_id")
    await database.ai_usage_logs.create_index("operation")


async def seed(reset: bool) -> None:
    await connect_to_database()

    try:
        database = get_database()

        if reset:
            for collection_name in (
                "tickets",
                "orders",
                "faqs",
                "ai_usage_logs",
            ):
                await database[collection_name].delete_many({})

        for order in load_json("orders.json"):
            prepared = prepare_order(order)
            await database.orders.replace_one(
                {"order_id": prepared["order_id"]},
                prepared,
                upsert=True,
            )

        for faq in load_json("faqs.json"):
            prepared = prepare_faq(faq)
            await database.faqs.replace_one(
                {"faq_id": prepared["faq_id"]},
                prepared,
                upsert=True,
            )

        await ensure_indexes(database)

        order_count = await database.orders.count_documents({})
        faq_count = await database.faqs.count_documents({})

        print(f"Database: {database.name}")
        print(f"Orders available: {order_count}")
        print(f"FAQs available: {faq_count}")
        print("Indexes: ready")
        print(
            "Mode: reset and seed"
            if reset
            else "Mode: idempotent upsert"
        )
    finally:
        await close_database()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed the SupportOps AI training database."
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear training collections before seeding.",
    )
    args = parser.parse_args()

    asyncio.run(seed(reset=args.reset))


if __name__ == "__main__":
    main()
