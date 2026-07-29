from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from {{ project_module }}.app.models import ExampleModel, fetch_example, fetch_examples
from {{ project_module }}.config.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["api", "examples"])


class ExampleResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: datetime
    updated_at: datetime | None

    @classmethod
    def from_example(cls, example: ExampleModel) -> "ExampleResponse":
        exclude_keys = ["ex_bool"]
        raw_values = example.model_dump()
        raw_values["email"] = "******"
        raw_values["id"] = str(raw_values["id"])
        resp_values = {k: v for k, v in raw_values.items() if k not in exclude_keys}
        return cls(**resp_values)


@router.get("/list", response_model=list[ExampleResponse])
def get_examples() -> list[ExampleResponse]:
    logger.info("/list endpoint was hit")
    logger.warning("test warning")
    logger.error("test error!")
    return [ExampleResponse.from_example(i) for i in fetch_examples()]


@router.get("/{ex_id}", response_model=ExampleResponse)
def get_ex_by_id(ex_id: str) -> ExampleResponse:
    ex = fetch_example(ex_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Example not found")
    return ExampleResponse.from_example(ex)
