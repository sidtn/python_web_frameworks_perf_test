from fastapi import FastAPI, HTTPException

from cache import clear_cache, get_cached_json, order_cache_key, set_cached_json
from db import AsyncSessionLocal
from orders_service import fetch_order_by_id, fetch_order_lite
from schemas import OrderResponse, OrderSchema

app = FastAPI()


@app.on_event("startup")
async def clear_cache_on_startup() -> None:
    await clear_cache()


@app.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int) -> OrderResponse:
    cache_key = order_cache_key(order_id, lite=False)
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return OrderResponse.model_validate_json(cached)

    async with AsyncSessionLocal() as session:
        data = await fetch_order_by_id(session, order_id)

    if data is None:
        raise HTTPException(status_code=404, detail="No orders found")

    await set_cached_json(cache_key, data.model_dump_json())
    return data


@app.get("/orders/{order_id}/lite", response_model=OrderSchema)
async def get_order_lite(order_id: int) -> OrderSchema:
    cache_key = order_cache_key(order_id, lite=True)
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return OrderSchema.model_validate_json(cached)

    async with AsyncSessionLocal() as session:
        data = await fetch_order_lite(session, order_id)

    if data is None:
        raise HTTPException(status_code=404, detail="No orders found")

    await set_cached_json(cache_key, data.model_dump_json())
    return data
