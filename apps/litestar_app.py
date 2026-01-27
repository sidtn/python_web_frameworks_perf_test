from litestar import Litestar, get

from cache import clear_cache, get_cached_json, order_cache_key, set_cached_json
from db import AsyncSessionLocal
from orders_service import fetch_order_by_id, fetch_order_lite
from schemas import OrderResponse, OrderSchema

@get("/orders/{order_id:int}")
async def get_order(order_id: int) -> dict:
    cache_key = order_cache_key(order_id, lite=False)
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return OrderResponse.model_validate_json(cached).model_dump()

    async with AsyncSessionLocal() as session:
        data = await fetch_order_by_id(session, order_id)

    if data is None:
        return {"detail": "No orders found"}

    await set_cached_json(cache_key, data.model_dump_json())
    return data.model_dump()


@get("/orders/{order_id:int}/lite")
async def get_order_lite(order_id: int) -> dict:
    cache_key = order_cache_key(order_id, lite=True)
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return OrderSchema.model_validate_json(cached).model_dump()

    async with AsyncSessionLocal() as session:
        data = await fetch_order_lite(session, order_id)

    if data is None:
        return {"detail": "No orders found"}

    await set_cached_json(cache_key, data.model_dump_json())
    return data.model_dump()

app = Litestar(route_handlers=[get_order, get_order_lite], on_startup=[clear_cache])
