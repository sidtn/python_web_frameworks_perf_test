# Python Frameworks Benchmark Results

This repo compares several web stacks serving the same endpoints and database schema.

## Schema

The database contains the following tables:
- `users`
- `addresses` (FK to `users`)
- `products`
- `orders` (FK to `users`, `addresses`)
- `order_items` (FK to `orders`, `products`)

Each order has 20 items via `order_items`.

## Cache

Each app uses Redis for response caching:
- `/orders/{order_id}` cached under `orders:{app}:full:{order_id}`
- `/orders/{order_id}/lite` cached under `orders:{app}:lite:{order_id}`

Cache is cleared on app startup for the given `APP_NAME` namespace.

## Endpoints

All apps expose:
- `/orders/{order_id}` (full join response)
- `/orders/{order_id}/lite` (order-only)

All apps use Postgres and Redis caching. Test runs were executed with the same K6 script (`script.js`).

## Results (Average of 3 runs)

Metrics are from K6 summary output:
- **Avg latency** = `http_req_duration avg`
- **P95 latency** = `http_req_duration p(95)`
- **Avg RPS** = `http_reqs / s`

| App | Runs | Avg latency (ms) | P95 latency (ms) | Avg RPS |
| --- | ---: | ---: | ---: | ---: |
| fastapi-granian | 3 | 1.407 | 3.013 | 13334 |
| fastapi-uvicorn | 3 | 4.933 | 15.973 | 3944 |
| litestar-granian | 3 | 1.473 | 3.697 | 12806 |
| litestar-uvicorn | 3 | 4.333 | 13.863 | 4411 |
| sanic-granian | 3 | 1.173 | 2.383 | 16129 |
| sanic-uvicorn | 3 | 3.883 | 14.770 | 4895 |

### Go (Gin)

| App | Runs | Avg latency (ms) | P95 latency (ms) | Avg RPS |
| --- | ---: | ---: | ---: | ---: |
| gin | 3 | 0.758 | 1.860 | 24333 |

## Notes
- Raw outputs live in `reports/`.
- All averages are computed across the three runs per app.
