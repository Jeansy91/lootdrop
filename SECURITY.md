# Security Policy

## Supported Versions

Only the latest release (and the `latest` image on ghcr.io) receives security fixes. Every relevant merge to `main` creates a new release automatically.

## Reporting a Vulnerability

Please **do not** open a public issue for security problems.

- If the repository's **Security** tab offers **Report a vulnerability**, use it to send a private report.
- Otherwise, contact the maintainer [@Jeansy91](https://github.com/Jeansy91) directly on GitHub.

Please include what is affected, how to reproduce it, and the impact you expect. You will get an answer within 7 days.

## Automated Checks

- **Dependabot** (`.github/dependabot.yml`) keeps Python packages, GitHub Actions and the Docker base image up to date. Patch and minor updates are merged automatically once CI passes; major updates wait for a manual review.
- **Security workflow** (`.github/workflows/security.yml`) runs on every push to `main`, on every pull request (as part of the build) and weekly:
  - `pip-audit` checks `requirements.txt` for known vulnerabilities.
  - `bandit` checks the Python code for insecure patterns.
  - `gitleaks` scans the whole Git history for committed secrets.

## Operating Lootdrop Securely

- Always set `SECRET_KEY` to a long random value and `ADMIN_PASSWORD` to a strong password. The built-in defaults are only for local development.
- Never commit `.env`. It is listed in `.gitignore`.
