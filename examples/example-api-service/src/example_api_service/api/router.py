from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from example_api_service.app.items import Item, get_item, list_items

router = APIRouter(prefix="/items", tags=["items"])


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str

    @classmethod
    def from_item(cls, item: Item) -> "ItemResponse":
        return cls(id=item.id, name=item.name, description=item.description)


@router.get("/", response_model=list[ItemResponse])
def get_items() -> list[ItemResponse]:
    return [ItemResponse.from_item(i) for i in list_items()]


@router.get("/{item_id}", response_model=ItemResponse)
def get_item_by_id(item_id: int) -> ItemResponse:
    item = get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return ItemResponse.from_item(item)