from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from example_api_service.api.router import router
from example_api_service.config.app_config import APP_CONFIG
from example_api_service.config.logging_config import configure_logging, get_logger

configure_logging(APP_CONFIG.LOG_LEVEL, APP_CONFIG.APP_ENV)
logger = get_logger(__name__)

app = FastAPI(title="Example API Service", description="A FastAPI service deployed to Cloud Run")
app.include_router(router)

logger.info(f"starting; service={APP_CONFIG.APP_NAME}; env={APP_CONFIG.APP_ENV}; log_level={APP_CONFIG.LOG_LEVEL}")


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


@app.get("/healthcheck", tags=["health"])
def healthcheck() -> dict:
    return {"status": "ok", "service": "example-api-service"}