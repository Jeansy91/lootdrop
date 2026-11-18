# Contributing to Lootdrop

Thanks for your interest in Lootdrop! Bug reports, ideas and pull requests are welcome.

## Reporting bugs and suggesting features

- Search the [existing issues](https://github.com/Jeansy91/lootdrop/issues) first.
- Use the issue templates for bug reports and feature requests.
- **Security problems** must not be reported in a public issue. Follow [SECURITY.md](SECURITY.md) instead.

## Development setup

Requirements: Python 3.12 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env, set DATABASE_PATH=./data/lootdrop.db
uvicorn app.main:app --reload
```

Run the tests before you open a pull request:

```bash
python -m unittest discover -s tests -v
```

## Code guidelines

- Routes in `app/routes/` only handle HTTP. Business logic belongs in `app/services/`.
- Keep each file focused on one responsibility.
- All user-facing text goes through `app/i18n.py` and needs both a German (`de`) and an English (`en`) translation.
- Keep changes small and focused. One pull request per topic.
- Add or update tests in `tests/` when you change behaviour.

## Commit messages

Lootdrop uses [Conventional Commits](https://www.conventionalcommits.org/). The commit types decide the next release version automatically (see the README section "Automatic releases"):

- `feat: ...` for a new feature
- `fix: ...` for a bug fix
- `docs:`, `test:`, `ci:`, `style:`, `chore:` for changes that do not need a release
- add `!` after the type (for example `feat!: ...`) for breaking changes

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Make your change, run the tests and update the documentation if needed.
3. Open a pull request and fill in the template.
4. CI must pass (tests on Python 3.12 to 3.15, `pip-audit`, `bandit`, `gitleaks` and the Docker build).

Pull requests are merged with a squash merge, so the pull request title should follow the commit message format above.
