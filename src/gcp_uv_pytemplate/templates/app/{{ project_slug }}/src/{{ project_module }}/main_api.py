import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response

from {{ project_module }}.api.router import router
from {{ project_module }}.config.app_config import APP_CONFIG
from {{ project_module }}.config.logging_config import configure_logging, get_logger

configure_logging(APP_CONFIG.LOG_LEVEL, APP_CONFIG.APP_ENV)
logger = get_logger(__name__)

app = FastAPI(title="{{ project_name }}", description="{{ project_description }}")
app.include_router(router)

logger.info("starting", service=APP_CONFIG.APP_NAME, env=APP_CONFIG.APP_ENV, log_level=APP_CONFIG.LOG_LEVEL)


@app.middleware("http")
async def logging_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    structlog.contextvars.clear_contextvars()

    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    trace_header = request.headers.get("X-Cloud-Trace-Context", "")
    trace_value = trace_header.split("/")[0] if trace_header else None

    ctx: dict = dict(request_id=request_id, method=request.method, path=request.url.path)
    if trace_value:
        ctx["logging.googleapis.com/trace"] = trace_value
    structlog.contextvars.bind_contextvars(**ctx)

    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)

    logger.info("request", status_code=response.status_code, duration_ms=duration_ms)
    return response


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> str:
    return """
    <!DOCTYPE html>
    <html>
        <head><title>{{ project_name }}</title></head>
        <body>
            <h1>{{ project_name }}</h1>
            <p>{{ project_description }}</p>
            <p><a href="/docs">API Docs</a></p>
        </body>
    </html>
    """


@app.get("/healthcheck", tags=["health"])
def healthcheck() -> dict:
    return {"status": "ok", "service": "{{ project_slug }}"}
