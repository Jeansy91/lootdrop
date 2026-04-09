Act as a Lead Software Architect focused on system modularization and LLM context efficiency.

Review all files against the project's coding principles, fix violations, and identify structural improvements that reduce token load per working step.

## Project Stack

- **Backend:** Python 3.14, FastAPI, SQLModel, APScheduler, Jinja2
- **Frontend:** Jinja2 templates, Tailwind CSS (CDN), vanilla JavaScript
- **DB:** SQLite via SQLModel
- **Services:** GamerPower API, SMTP email

## Coding Principles to enforce

**Atomic Files — one responsibility per file**
- Each file has one clear purpose: route, service, model, template, or config — never mixed
- Routes only handle HTTP; business logic belongs in `app/services/`
- If a file has grown beyond its original scope, split it
- Goal: each module is self-contained and understandable without the full project as context

**Minimal code — no ballast**
- Remove dead code: commented-out blocks, unused variables, obsolete imports
- Remove over-abstraction: helpers or wrappers created for a single use case
- Remove unnecessary error handling for scenarios that cannot happen
- Merge duplicate logic (e.g. repeated `_ctx()` patterns across routes)

**Precise naming — unified naming scheme**
- Files, functions, variables must have descriptive, self-evident names
- Apply consistent naming across routes, services, models, and templates
- Remove redundant comments where the name already documents the intent
- German comments only in templates (user-facing), English everywhere else

**Clean interfaces & entry points**
- Keep `app/main.py` minimal — only lifespan, middleware, router registration
- Services expose a clean public API; internals prefixed with `_`
- Avoid importing models directly in templates — pass all data via route context

**Consistency**
- Styling: Tailwind CSS classes only — no inline styles
- JavaScript: vanilla only, no frameworks; state via `localStorage` where persistence is needed
- i18n: all user-facing strings go through `app/i18n.py` — no hardcoded strings in templates or JS (except interpolated via `{{ t(...) }}`)
- Platform color map defined once — currently duplicated between Jinja template and JS; consolidate

**Database**
- Schema changes go through `migrate()` in `app/database.py` — never raw SQL elsewhere
- Models stay in `app/models.py`; no business logic in model classes

## Steps

1. Run `git log origin/main..HEAD --oneline` to identify unpushed commits, then `git diff origin/main HEAD` to see all changed files and their diffs
2. For each changed file, identify violations of the principles above
3. Fix every violation directly in the file
4. Flag any structural issues (wrong file placement, duplicated logic, bloated templates) that require larger refactoring — describe the problem and the recommended split/move, but do not execute large restructuring automatically
5. Report a brief summary of what was fixed and what structural improvements are recommended
