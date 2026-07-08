from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, EmailStr


class ExampleModel(BaseModel):
    """Example pydantic Model"""
    
    model_config = ConfigDict(str_strip_whitespace=True)

    id: UUID = Field(default_factory=uuid4, description="Auto-generated unique UUID4 id.")
    name: str = Field(min_length=1, max_length=200, description="Name, non-empty string with min/max validation.")
    email: EmailStr
    ex_bool: bool = Field(default=True, description="Example bool")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default=None)


# In-memory store and simple fetch examples — replace with a real DB or service client
_examples: list[ExampleModel] = [
    ExampleModel(id="46914fde-89c3-4054-8e97-7c131adfff3f", name="Jason", email="jason@fake.com", ex_bool=False),
    ExampleModel(id="e3c40fef-ac0f-4748-ad13-4df3017c3c2c", name="Maya", email="maya@fake.com"),
]

def fetch_examples() -> list[ExampleModel]:
    return _examples


def fetch_example(id: str) -> ExampleModel | None:
    try:
        target_id = UUID(id)
    except ValueError:
        return None
    return next((i for i in _examples if i.id == target_id), None)