import typer
from rich.console import Console
from rich.table import Table

from {{ project_module }}.app.items import get_item, list_items

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command()
def items() -> None:
    """List all items."""
    table = Table("ID", "Name", "Description")
    for item in list_items():
        table.add_row(str(item.id), item.name, item.description)
    console.print(table)


@app.command()
def item(item_id: int = typer.Argument(..., help="Item ID to fetch")) -> None:
    """Get a single item by ID."""
    result = get_item(item_id)
    if not result:
        console.print(f"[red]Item {item_id} not found.[/red]")
        raise typer.Exit(code=1)
    console.print(f"[bold]{result.id}[/bold] — {result.name}: {result.description}")
