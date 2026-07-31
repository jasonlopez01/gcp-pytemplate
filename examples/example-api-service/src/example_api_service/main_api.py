import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response

from example_api_service.api.router import router
from example_api_service.config.app_config import APP_CONFIG
from example_api_service.config.gcp_env import GCP_ENV_DATA
from example_api_service.config.logging_config import configure_logging, get_logger

configure_logging(APP_CONFIG.LOG_LEVEL, APP_CONFIG.APP_ENV, service=APP_CONFIG.APP_NAME)
logger = get_logger(__name__)

app = FastAPI(title="Example API Service", description="A FastAPI service deployed to Cloud Run")
app.include_router(router)

logger.info("starting", log_level=APP_CONFIG.LOG_LEVEL)


@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    structlog.contextvars.clear_contextvars()

    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    trace_header = request.headers.get("X-Cloud-Trace-Context", "")
    trace_value = trace_header.split("/")[0] if trace_header else None

    ctx: dict = dict(request_id=request_id, method=request.method, path=request.url.path)
    if trace_value and GCP_ENV_DATA.IS_DEPLOYED:
        # Cloud Logging only links logs to a trace when the value is the full resource path.
        ctx["logging.googleapis.com/trace"] = f"projects/{GCP_ENV_DATA.GCP_PROJECT}/traces/{trace_value}"
    structlog.contextvars.bind_contextvars(**ctx)

    start = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception:
        # Without this an unhandled handler error leaves no request log at all, just the
        # traceback from the server's own error handling.
        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.exception("request failed", duration_ms=duration_ms)
        raise

    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info("request", status_code=response.status_code, duration_ms=duration_ms)
    return response


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index() -> str:
    return """
    <!DOCTYPE html>
    <html>
        <head><title>Example API Service</title></head>
        <body>
            <h1>Example API Service</h1>
            <p>A FastAPI service deployed to Cloud Run</p>
            <p><a href="/docs">API Docs</a></p>
        </body>
    </html>
    """


@app.get(APP_CONFIG.HEALTH_CHECK_ROUTE, tags=["health"])
def healthcheck() -> dict:
    # Sourced from config rather than baked in, so the response follows APP_CONFIG_FILE.
    return {"status": "ok", "service": APP_CONFIG.APP_NAME, "env": APP_CONFIG.APP_ENV}
