from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy import insert, select

from db import Base, engine

NUM_USERS = 100
NUM_PRODUCTS = 100_000
NUM_ORDERS = 1_000_000
ITEMS_PER_ORDER = 20
ORDERS_BATCH_SIZE = 1_000
PRODUCTS_BATCH_SIZE = 5_000


def price_for_index(index: int) -> Decimal:
    cents = 100 + (index % 10_000)
    return Decimal(cents) / Decimal(100)


async def main() -> None:
    users_table = Base.metadata.tables["users"]
    addresses_table = Base.metadata.tables["addresses"]
    products_table = Base.metadata.tables["products"]
    orders_table = Base.metadata.tables["orders"]
    order_items_table = Base.metadata.tables["order_items"]

    user_ids: list[int] = []
    address_ids: list[int] = []
    product_ids: list[int] = []
    product_prices: list[Decimal] = []

    async with engine.begin() as conn:
        users_batch = []
        for i in range(NUM_USERS):
            users_batch.append(
                {
                    "email": f"user{i}@example.com",
                    "full_name": f"User {i}",
                }
            )
        await conn.execute(insert(users_table), users_batch)
        user_ids = list(
            await conn.scalars(select(users_table.c.id).order_by(users_table.c.id))
        )

        addresses_batch = []
        for i, user_id in enumerate(user_ids):
            addresses_batch.append(
                {
                    "user_id": user_id,
                    "line1": f"{100 + i} Main St",
                    "line2": None,
                    "city": "Testville",
                    "state": "CA",
                    "postal_code": f"{90000 + i:05d}",
                }
            )
        await conn.execute(insert(addresses_table), addresses_batch)
        address_ids = list(
            await conn.scalars(
                select(addresses_table.c.id).order_by(addresses_table.c.id)
            )
        )

        for offset in range(0, NUM_PRODUCTS, PRODUCTS_BATCH_SIZE):
            batch = []
            batch_end = min(offset + PRODUCTS_BATCH_SIZE, NUM_PRODUCTS)
            for i in range(offset, batch_end):
                price = price_for_index(i)
                product_prices.append(price)
                batch.append(
                    {
                        "name": f"Product {i}",
                        "sku": f"SKU{i:06d}",
                        "price": price,
                    }
                )
            await conn.execute(insert(products_table), batch)
        product_ids = list(
            await conn.scalars(select(products_table.c.id).order_by(products_table.c.id))
        )

        orders_per_user = NUM_ORDERS // NUM_USERS
        order_index = 0
        orders_batch = []
        items_batch = []

        for user_idx, user_id in enumerate(user_ids):
            address_id = address_ids[user_idx]
            for _ in range(orders_per_user):
                item_total = Decimal("0")
                base = (order_index * ITEMS_PER_ORDER) % NUM_PRODUCTS
                for j in range(ITEMS_PER_ORDER):
                    product_idx = (base + j) % NUM_PRODUCTS
                    unit_price = product_prices[product_idx]
                    item_total += unit_price
                    items_batch.append(
                        {
                            "order_id": None,
                            "product_id": product_ids[product_idx],
                            "quantity": 1,
                            "unit_price": unit_price,
                        }
                    )

                orders_batch.append(
                    {
                        "user_id": user_id,
                        "address_id": address_id,
                        "quantity": ITEMS_PER_ORDER,
                        "status": "pending",
                        "total": item_total,
                    }
                )

                order_index += 1

                if len(orders_batch) >= ORDERS_BATCH_SIZE:
                    result = await conn.execute(
                        insert(orders_table).returning(orders_table.c.id),
                        orders_batch,
                    )
                    order_ids_batch = list(result.scalars())
                    for idx, order_id in enumerate(order_ids_batch):
                        base_idx = idx * ITEMS_PER_ORDER
                        for item_idx in range(base_idx, base_idx + ITEMS_PER_ORDER):
                            items_batch[item_idx]["order_id"] = order_id

                    await conn.execute(insert(order_items_table), items_batch)
                    orders_batch.clear()
                    items_batch.clear()

        if orders_batch:
            result = await conn.execute(
                insert(orders_table).returning(orders_table.c.id),
                orders_batch,
            )
            order_ids_batch = list(result.scalars())
            for idx, order_id in enumerate(order_ids_batch):
                base_idx = idx * ITEMS_PER_ORDER
                for item_idx in range(base_idx, base_idx + ITEMS_PER_ORDER):
                    items_batch[item_idx]["order_id"] = order_id

            await conn.execute(insert(order_items_table), items_batch)


if __name__ == "__main__":
    asyncio.run(main())
