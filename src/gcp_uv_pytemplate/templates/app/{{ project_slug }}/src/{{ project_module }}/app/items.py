from dataclasses import dataclass, field


@dataclass
class Item:
    id: int
    name: str
    description: str


# In-memory store — replace with a real DB or service client
_items: list[Item] = [
    Item(id=1, name="Widget", description="A standard widget"),
    Item(id=2, name="Gadget", description="A fancy gadget"),
]


def list_items() -> list[Item]:
    return _items


def get_item(item_id: int) -> Item | None:
    return next((i for i in _items if i.id == item_id), None)
