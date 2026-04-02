from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from {{ project_module }}.api.router import router
from {{ project_module }}.config.app_config import APP_CONFIG
from {{ project_module }}.config.logging_config import configure_logging, get_logger

configure_logging(APP_CONFIG.LOG_LEVEL, APP_CONFIG.APP_ENV)
logger = get_logger(__name__)

app = FastAPI(title="{{ project_name }}", description="{{ project_description }}")
app.include_router(router)

logger.info(f"starting; service={APP_CONFIG.APP_NAME}; env={APP_CONFIG.APP_ENV}; log_level={APP_CONFIG.LOG_LEVEL}")


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
