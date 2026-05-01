# gcp-pytemplate — Agent Guide

A CLI tool that scaffolds production-ready GCP Python projects. It renders a Jinja2 template tree into a new project directory.

## Commands

Use `make` for all core operations.

| Command | Description |
|---|---|
| `make setup` | Install dependencies and git hooks |
| `make install` | Install CLI and MCP server globally as editable (source changes apply immediately) |
| `make lint` | Lint and autoformat (ruff) |
| `make test` | Run tests |
| `make test-all` | Run tests against all supported Python versions (3.10–3.14) |
| `make generate-examples` | Regenerate `examples/` from the YAML files in `examples/*.yaml` |

Do not invoke `uv`, `ruff`, or `pytest` directly — use the make targets above.

### MCP server

```bash
gcp-pytemplate-mcp   # starts the stdio MCP server (requires the [mcp] extra)
```

See the **MCP Server** section in `README.md` for installation and client config.

### Running the CLI

```bash
uv run gcp-pytemplate new                              # interactive prompts
uv run gcp-pytemplate new --from-file examples/api_project.yaml
uv run gcp-pytemplate update <project-path> --components logging_config
```

## Project Layout

- `src/gcp_pytemplate/main.py` — Typer CLI (`new` and `update` commands), input validation, Jinja2 context assembly
- `src/gcp_pytemplate/render.py` — walks the template tree, renders file contents and paths with Jinja2
- `src/gcp_pytemplate/templates/app/{{ project_slug }}/` — the project template (Jinja2; not valid Python until rendered)
- `examples/` — pre-generated example projects (`example-api-service`, `example-cli-job`) plus the YAML inputs used to generate them
- `src/gcp_pytemplate/mcp_server.py` — MCP server (`create_project`, `update_project`, `list_components` tools)
- `tests/` — `test_render.py` (template output), `test_update.py` (update command), `test_mcp_server.py` (MCP tools)

## Coding Standards

**Use Pydantic for data modeling.** Prefer `pydantic.BaseModel` over native `@dataclass` for any structured data (config objects, request/response shapes, context models). Use `model_validator` and `field_validator` for validation logic rather than `__post_init__`. Pydantic models are the single source of truth for schema, validation, and serialization.

**Use modern Python type hints.** Target Python 3.10+ syntax throughout:
- Built-in generics: `list[str]`, `dict[str, int]`, `tuple[str, ...]` — not `List`, `Dict`, `Tuple` from `typing`
- Union shorthand: `str | None` — not `Optional[str]` or `Union[str, None]`
- `typing.Any`, `typing.Literal`, `typing.TypeVar`, `typing.Protocol` are still fine where needed
- Annotate all function signatures (parameters and return types); omit only where the type is genuinely unknowable

**Write pytest-style tests.** Use plain functions (`def test_*`) and `assert` statements — no `unittest.TestCase`. Fixtures go in `conftest.py`. Parametrize with `@pytest.mark.parametrize` rather than looping inside a test. Use `tmp_path` for filesystem fixtures. Avoid mocking internals; test at the public API surface.

## Key Rules

**CLI and MCP server must stay in sync.** When adding or changing inputs to the `new` command in `main.py` (parameters, defaults, validation, resolution logic), apply the equivalent change to `create_project` in `mcp_server.py`. Both share `_build_context()` for validation, but default resolution (e.g. git/gcloud config lookups) and the elicitation summary in `_format_summary` must be updated manually to match.

**Templates and examples must stay in sync.** When editing any file under `templates/`, apply the equivalent change to the corresponding file in `examples/example-api-service/` and/or `examples/example-cli-job/`. Alternatively, run `make generate-examples` to fully regenerate both examples (only appropriate when the change should affect all generated content, not for manual example-specific edits).

**Templates are excluded from ruff.** Files under `src/gcp_pytemplate/templates/` contain Jinja2 syntax and are not valid Python — ruff is configured to skip them. Don't run linting on template files.

**Keep documentation in sync.** When making changes that affect functionality or interfaces (CLI flags, MCP tools, Python version support, make targets, project layout), update `README.md` and `AGENTS.md` to match. The Prerequisites, Usage, and Development sections of `README.md` and the Commands table in `AGENTS.md` are the primary places to check.

**Commit style: conventional commits.** Pre-commit hooks enforce the format. Prefixes and their effect on versioning and the changelog:

| Prefix | Version bump | In changelog |
|---|---|---|
| `feat:` | minor | yes |
| `fix:`, `perf:` | patch | yes |
| `docs:` | none | yes |
| `chore:`, `ci:`, `style:`, `test:`, `refactor:` | none | no |

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
