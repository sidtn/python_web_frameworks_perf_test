FASTAPI_APP=apps.fastapi_app:app
LITESTAR_APP=apps.litestar_app:app
SANIC_APP=apps.sanic_app:app


.PHONY: fastapi sanic litestar

fastapi-uvicorn:
	APP_NAME=fastapi uvicorn $(FASTAPI_APP) --host 0.0.0.0 --port 8000 --workers 10

fastapi-granian:
	APP_NAME=fastapi granian --interface asgi $(FASTAPI_APP) --host 0.0.0.0 --port 8000 --workers 10

sanic-uvicorn:
	APP_NAME=sanic uvicorn $(SANIC_APP) --host 0.0.0.0 --port 8000 --workers 10

sanic-granian:
	APP_NAME=sanic granian --interface asgi $(SANIC_APP) --host 0.0.0.0 --port 8000 --workers 10

litestar-uvicorn:
	APP_NAME=litestar uvicorn $(LITESTAR_APP) --host 0.0.0.0 --port 8000 --workers 10

litestar-granian:
	APP_NAME=litestar granian --interface asgi $(LITESTAR_APP) --host 0.0.0.0 --port 8000 --workers 10

gin-go:
	APP_NAME=gin PORT=8000 go run ./go_app
