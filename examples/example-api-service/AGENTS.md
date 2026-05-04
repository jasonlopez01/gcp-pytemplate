# Example API Service — Agent Guide

## Commands

Use `make` for all core operations. Run `make help` to list everything available.

| Command | Description |
|---|---|
| `make setup` | Install dependencies |
| `make lint` | Lint and autoformat (ruff) |
| `make test` | Run tests |
| `make start-api` | Start FastAPI locally on port 8080 |
| `make deploy_gcr DEPLOY_CONFIG=<file>` | Deploy to Cloud Run |

Do not invoke `uv`, `ruff`, `pytest`, or `uvicorn` directly — use the make targets above.

## Configuration

Runtime config is loaded from `config/app_configs/` via the `APP_CONFIG_FILE` env var. The `make start-api` target defaults to `local.env`. Set it explicitly when needed:

```bash
APP_CONFIG_FILE=stage.env make start-api
```

## Project Layout

- `src/example_api_service/` — application source
  - `main_api.py` — FastAPI entrypoint
  - `api/` — routes and router
  - `app/` — shared business logic
  - `config/` — app config, logging config, GCP env detection
- `deploy_configs/` — per-environment deploy settings (`stage`, `prod`)
- `scripts/` — deployment shell scripts (invoked via make)

## Key Rules

**Keep documentation in sync.** When making changes that affect functionality or interfaces (API request/responses, CLI flags, MCP tools, Python version support, make targets, project layout), update `README.md` and `AGENTS.md` to match. The Prerequisites, Usage, and Development sections of `README.md` and the Commands table in `AGENTS.md` are the primary places to check.


## Coding Standards

**Use Pydantic for data modeling.** Prefer `pydantic.BaseModel` over native `@dataclass` for any structured data (config objects, request/response shapes, context models). Use `model_validator` and `field_validator` for validation logic rather than `__post_init__`. Pydantic models are the single source of truth for schema, validation, and serialization.

**Use modern Python type hints.** Target Python 3.10+ syntax throughout:
- Built-in generics: `list[str]`, `dict[str, int]`, `tuple[str, ...]` — not `List`, `Dict`, `Tuple` from `typing`
- Union shorthand: `str | None` — not `Optional[str]` or `Union[str, None]`
- `typing.Any`, `typing.Literal`, `typing.TypeVar`, `typing.Protocol` are still fine where needed
- Annotate all function signatures (parameters and return types); omit only where the type is genuinely unknowable

**Write pytest-style tests.** Use plain functions (`def test_*`) and `assert` statements — no `unittest.TestCase`. Fixtures go in `conftest.py`. Parametrize with `@pytest.mark.parametrize` rather than looping inside a test. Use `tmp_path` for filesystem fixtures. Avoid mocking internals; test at the public API surface.

## SQL Conventions

**Use fully qualified resource paths.** Always reference tables with their full path — no bare table names:
- BigQuery: `project.dataset.table`
- Other databases: `database.schema.table`

**Use lowercase keywords.** Write all SQL keywords in lowercase: `select`, `from`, `where`, `join`, `group by`, `order by`, etc.

**Use single spaces around aliases.** No alignment padding — exactly one space on each side of `as`:
```sql
-- correct
select
    order_id as id,
    customer_name as name
from project.dataset.orders

-- wrong
select
    order_id     as id,
    customer_name as name
from project.dataset.orders
```

**Use trailing commas.** Place commas at the end of each item in a select list, not the beginning.

**Indent with 4 spaces.** Indent column lists and `on` clauses 4 spaces relative to their clause keyword.


## Writing Style

**Avoid AI tells.** Comments, docs, commit messages, and PR descriptions should read like they were written by a developer, not generated. Specific patterns to avoid:

- No em-dashes (`—`). Use a comma, semicolon, colon, or rewrite the sentence.
- No filler openers: "Certainly", "Sure", "Of course", "Absolutely", "Great", "Happy to help".
- No over-explanation of obvious things. If the code is clear, don't restate it in a comment.
- No "This commit..." or "This PR..." prefix in commit/PR titles. Start with the verb: "Add", "Fix", "Remove", "Update".
- No closing affirmations: "Let me know if you have questions", "Hope this helps", "Feel free to reach out".
- Prefer plain words over formal ones: "use" not "utilize", "show" not "demonstrate", "check" not "verify" when the meaning is the same.