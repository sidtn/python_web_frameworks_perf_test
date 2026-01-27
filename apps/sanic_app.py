from __future__ import annotations

import json as pyjson

from sanic import Sanic
from sanic.response import json

from cache import clear_cache, get_cached_json, order_cache_key, set_cached_json
from db import AsyncSessionLocal
from orders_service import fetch_order_by_id, fetch_order_lite

app = Sanic("perf_test")


@app.before_server_start
async def clear_cache_on_startup(app):
    await clear_cache()

@app.get("/orders/<order_id:int>")
async def get_order(request, order_id: int):
    cache_key = order_cache_key(order_id, lite=False)
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return json(pyjson.loads(cached), status=200)

    async with AsyncSessionLocal() as session:
        data = await fetch_order_by_id(session, order_id)

    if data is None:
        return json({"detail": "No orders found"}, status=404)

    await set_cached_json(cache_key, data.model_dump_json())
    return json(data.model_dump())


@app.get("/orders/<order_id:int>/lite")
async def get_order_lite(request, order_id: int):
    cache_key = order_cache_key(order_id, lite=True)
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return json(pyjson.loads(cached), status=200)

    async with AsyncSessionLocal() as session:
        data = await fetch_order_lite(session, order_id)

    if data is None:
        return json({"detail": "No orders found"}, status=404)

    await set_cached_json(cache_key, data.model_dump_json())
    return json(data.model_dump())
