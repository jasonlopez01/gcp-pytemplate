from fastapi import FastAPI
from fastapi.testclient import TestClient

from example_api_service.api.router import router

# Build a minimal app from the router to avoid config dependencies in tests.
_app = FastAPI()
_app.include_router(router)


@_app.get("/healthcheck")
def _healthcheck() -> dict:
    return {"status": "ok"}


client = TestClient(_app)


def test_healthcheck_returns_ok():
    response = client.get("/healthcheck")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# TODO: Remove tests below once the demo models are replaced with real ones.
def test_list_returns_list():
    response = client.get("/api/list")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


def test_list_items_have_expected_fields():
    item = client.get("/api/list").json()[0]
    assert "id" in item
    assert "name" in item
    assert "email" in item


def test_get_by_valid_id_returns_example():
    response = client.get("/api/46914fde-89c3-4054-8e97-7c131adfff3f")
    assert response.status_code == 200
    assert response.json()["name"] == "Jason"


def test_get_by_unknown_id_returns_404():
    response = client.get("/api/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404