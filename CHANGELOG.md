# CHANGELOG

<!-- version list -->

## v0.1.1 (2026-08-08)

### Bug Fixes

- Cap the mcp dependency below 2.0
  ([`bf3cbdd`](https://github.com/jasonlopez01/gcp-pytemplate/commit/bf3cbdd0433c59793a81ed2d654881154ac3577a))

mcp 2.0.0 dropped mcp.server.fastmcp, which mcp_server.py imports, so a fresh `pip install
  gcp-pytemplate[mcp]` resolved to 2.0.0 and failed at import with ModuleNotFoundError. The 0.1.0
  release shipped with this broken.

It was invisible locally because uv.lock pinned a working 1.x, so only users installing from PyPI
  hit it. Cap the extra and the dev group at <2.0.0, keeping them in step.

Verified against a freshly built wheel: pip resolves mcp 1.29.0 and all four tools load. Migrating
  to the 2.x API is a separate piece of work.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

- Stop compiled artefacts leaking into generated projects
  ([`f7b2933`](https://github.com/jasonlopez01/gcp-pytemplate/commit/f7b29335ddcc7a294b7f8d3a96c348516c91653e))

pip byte-compiles every .py it installs, including the template tree, so an installed copy grows
  __pycache__ directories beside the templates. The renderer copied those straight through, and a
  project scaffolded from the published wheel came out with 15 stray .pyc files.

Skip any path containing __pycache__.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

### Documentation

- Add badges, PyPI project links and template attribution
  ([`3408d07`](https://github.com/jasonlopez01/gcp-pytemplate/commit/3408d07aa3bf1be8fddd0996646ba82b31c56973))

Adds a Tests status badge and a PyPI version badge to the README, and a [project.urls] table so the
  PyPI page gets sidebar links to the repo, issues and changelog. 0.1.0 published with no project
  URLs at all.

Generated projects now end their README with a line crediting gcp-pytemplate. Kept in the footer
  rather than the header so it does not sit above the user's own project description.

Also trims the longer explanatory comments added recently down to the point rather than the full
  reasoning behind each change.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>


## v0.1.0 (2026-08-06)

### Bug Fixes

- Guard destructive scaffolding and repair generated project defects
  ([`20be16b`](https://github.com/jasonlopez01/gcp-pytemplate/commit/20be16b8212ae0e155e9acfbf5787b9c2133102e))

The MCP create_project tool silently overwrote an existing project's files. It now refuses a
  non-empty target unless overwrite=true, validates input before prompting, and warns in the
  confirmation summary when it will replace a directory. The CLI gained a matching --overwrite flag.

A project name consisting only of punctuation slugified to "", which resolved the project root back
  to the output directory itself; confirming the overwrite prompt then deleted that directory.
  Project names are now rejected unless they produce an importable module name.

Jinja2 strips the final newline by default, so every rendered file was written without one and
  generated projects failed their own ruff format check. Render with keep_trailing_newline and fix
  the template lint errors this exposed, plus the trailing blank lines it surfaced in the Makefile
  and deploy configs.

gcp_env raised a ValidationError at import when a runtime set a service name but no revision, and an
  unreachable metadata server took the whole app down. It also stamped "not-set" over real
  GCP_PROJECT and GCP_REGION values on local runs; the export is now gated on IS_DEPLOYED and never
  overwrites.

Also corrects the documented Python version: the tool needs 3.10+, but generated projects pin 3.13+.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

- Handle non-text files in the template tree
  ([`d22c21c`](https://github.com/jasonlopez01/gcp-pytemplate/commit/d22c21ca1bf33b5a842a0ea572357b86c368371f))

A .DS_Store inside the template root aborted the whole render with an uncaught UnicodeDecodeError.
  Because it sorts first, no files were written at all, and the traceback did not name the offending
  file. Only jinja2.TemplateError was caught, so the decode error escaped.

Skip OS metadata by name, since it should never reach a generated project, and fall back to copying
  any file that is not valid UTF-8 rather than trying to render it. Binary assets in the template
  now pass through untouched.

Pin the read and write encoding to UTF-8 and write with newline="" so output does not depend on the
  host locale, and so rendered shell scripts and Procfiles keep LF endings on Windows hosts instead
  of gaining CRLF.

render_service takes an optional template_root so tests can render a fixture tree instead of the
  packaged one; the five new tests each fail against the specific defect they cover.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

- Keep per-machine Claude Code settings out of the sdist
  ([`a975aa1`](https://github.com/jasonlopez01/gcp-pytemplate/commit/a975aa1b00cf449e7486afaa94af119b14822cad))

.claude/settings.local.json was reaching the published sdist, carrying local absolute paths. It is
  untracked only because of a user-level global gitignore, which hatchling does not read.

Ignore it in the repo and exclude /.claude from the sdist target so the result does not depend on
  how an individual clone is configured.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

- Pin example authors so regeneration is user-independent
  ([`850d24c`](https://github.com/jasonlopez01/gcp-pytemplate/commit/850d24c4dc592d87276be1be1636b6b882ca3756))

The example YAML inputs omitted author_name and author_email, so 'new' fell back to the git config
  of whoever ran make generate-examples and wrote that identity into each example's pyproject.toml
  and .gcp-pytemplate.yaml.

Set both fields explicitly to a documentation address (RFC 2606) so the examples regenerate
  byte-identically for any contributor.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

- Rename the template pyproject so tooling stops parsing it
  ([`4854701`](https://github.com/jasonlopez01/gcp-pytemplate/commit/4854701cd3100663f7c317fa00c5a465d8f854dd))

GitHub's dependency graph scans the repo for manifests by filename, found
  src/gcp_pytemplate/templates/app/{{ project_slug }}/pyproject.toml, and failed on the Jinja2
  syntax. That produced a failing "Graph Update: pip in ..." job on every scan. Dependabot config
  cannot exclude a path from the graph, so the file has to stop looking like a manifest.

render.py now strips a trailing .jinja from the rendered path, and the template is named
  pyproject.toml.jinja. Stripping happens before the exclusion rules are evaluated so those rules
  stay written against final paths.

Rendered output is unchanged: both examples regenerate byte-identically, and a project scaffolded
  from the built wheel still produces a parseable pyproject.toml with no .jinja files left behind.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

- Serve the health check at the configured route
  ([`28193f8`](https://github.com/jasonlopez01/gcp-pytemplate/commit/28193f8b867b430debc974f72fea373f51292039))

HEALTH_CHECK_ROUTE was defined in app_config and set in the app config env files, but main_api
  hardcoded "/healthcheck", so changing the setting had no effect. Bind the route to
  APP_CONFIG.HEALTH_CHECK_ROUTE and read it from the same config in the generated test.

invoke_cloud_run.sh --health also assumed the default path. It now resolves the route from the app
  config named by the deploy config, falling back to /healthcheck, so the shorthand keeps working on
  a customized route.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

- Validate update paths and fail cleanly without a terminal
  ([`3b8f40d`](https://github.com/jasonlopez01/gcp-pytemplate/commit/3b8f40d5871d56e92ec6092fb90421273e76e0eb))

The MCP update_project tool rejected absolute and parent-relative --files paths, but the CLI update
  command did not, and an absolute path there crashed with an unhandled ValueError from relative_to
  when printing results. Move the check into a shared _validate_rel_paths helper so both entry
  points enforce it.

The questionary prompts also raised an opaque OSError with a full traceback when stdin was not a
  terminal, which made scripted use of new and update unusable. Fall back to the documented defaults
  for the interfaces and deploy target prompts, decline the overwrite prompt (pointing at
  --overwrite), and require --components or --files for update. Aborting because the target exists
  now exits 1 instead of 0.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

### Documentation

- Add security and codeowners
  ([`b3741d1`](https://github.com/jasonlopez01/gcp-pytemplate/commit/b3741d128d6240c17b9a4a0a8403571d96b55a01))

- Correct the deploy script referenced by execute_cloud_run_job
  ([`81eccc1`](https://github.com/jasonlopez01/gcp-pytemplate/commit/81eccc1baaac666e0f3aafd6ae493d4fdc15c42e))

The requirements comment pointed at deploy_job_from_image.sh, which is not part of the template; the
  script that deploys the job is deploy_cloud_run_job.sh.

Also record why args travel in an env var, and that --update-env-vars on 'jobs execute' is a
  per-execution override rather than an edit to the deployed job definition.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

- Update agent guides
  ([`0730b28`](https://github.com/jasonlopez01/gcp-pytemplate/commit/0730b28848969191f562e67504520cbb3b6e28c5))

- Update docs
  ([`d583193`](https://github.com/jasonlopez01/gcp-pytemplate/commit/d583193bca7784dc9451fb163633ef0393a5d1f6))

- Update examples
  ([`b583a45`](https://github.com/jasonlopez01/gcp-pytemplate/commit/b583a45454b798eb0bb9ed6fd542b650614993bc))

- Update notes
  ([`0c0404f`](https://github.com/jasonlopez01/gcp-pytemplate/commit/0c0404f84b1865d034aeef262e3ff8b96e51721e))

- Update readmes
  ([`7d3ab3d`](https://github.com/jasonlopez01/gcp-pytemplate/commit/7d3ab3ddcbc8b2c29ef8bcca8c578f30d9c361d5))

### Features

- Collect an author name only, never an email
  ([`9bd8e7c`](https://github.com/jasonlopez01/gcp-pytemplate/commit/9bd8e7c7ffa53ef39079da12a9bc6fbfab86f94d))

Author was the one input resolved silently: gcp_project, gcp_region and gcp_service_account are all
  prompted with a visible default, while name and email were read from git config and written into
  the generated project without ever being shown. Prompt for the name with git config as the default
  so the identity that lands in pyproject.toml is always something the user saw, and drop email
  collection entirely. Users who want an email published can add the key to their pyproject.toml by
  hand.

The generated authors block is now conditional. An empty entry is a hard build failure ("Author #1
  of field project.authors must specify either name or email"), which create_project could already
  produce on a machine with no git identity because it fell back to empty strings while the CLI fell
  back to placeholder text. Both now agree, and the field is omitted rather than emitted blank.

Removes the --author-email flag and the author_email tool argument.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>

- Log unhandled request errors and report env in the health check
  ([`8e2c6c3`](https://github.com/jasonlopez01/gcp-pytemplate/commit/8e2c6c38320f8fb8a25dfe7f10faeab03bbd49fb))

The request logging middleware wrapped call_next without a handler, so an unhandled error in a route
  produced no request log line at all, only the server's own traceback. Wrap it, emit the failure
  with its duration, and re-raise.

The health check hardcoded the project slug as the service name, which drifts from whatever APP_NAME
  the loaded config sets. Source both the service name and the environment from APP_CONFIG so the
  response follows APP_CONFIG_FILE.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
