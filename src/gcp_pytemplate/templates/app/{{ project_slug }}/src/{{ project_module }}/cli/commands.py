import typer
from rich.console import Console
from rich.table import Table

from {{ project_module }}.app.models import ExampleModel, fetch_example, fetch_examples
from {{ project_module }}.config.logging_config import get_logger

app = typer.Typer(no_args_is_help=True)
console = Console()
logger = get_logger(__name__)


@app.command()
def list_examples() -> None:
    """List all examples."""
    logger.info("list_examples command invoked")
    logger.warning("test warning")
    logger.error("test error!")
    field_names = [x.capitalize() for x in ExampleModel.model_fields.keys()]
    table = Table(*field_names)
    for ex in fetch_examples():
        ex_values = [str(x) for x in ex.model_dump().values()]
        table.add_row(*ex_values)
    console.print(table)


@app.command()
def get_example(id: str = typer.Argument(help="Example ID to fetch")) -> None:
    """Get a single example by ID."""
    result = fetch_example(id=id)
    if not result:
        logger.error("example not found", example_id=id)
        raise typer.Exit(code=1)
    console.print(f"[bold]{result.id}[/bold] — {result.name} ({result.email})")
