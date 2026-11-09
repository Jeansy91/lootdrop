# Lootdrop

Lootdrop aggregates free game giveaways from the GamerPower API and sends a daily email digest to subscribers. Subscribers can filter by platform and choose their preferred language (German or English).

## Features

- Automatic giveaway sync from the GamerPower API on a configurable interval
- Daily email digest with new giveaways (configurable send time)
- Platform filtering per subscriber
- Two languages: German (de) and English (en)
- Email preferences page: change language, platforms, or unsubscribe
- Admin panel for managing giveaways, subscribers, and settings

## Stack

- **Backend**: FastAPI, SQLModel, APScheduler
- **Database**: SQLite
- **Templates**: Jinja2, Tailwind CSS (CDN)
- **Email**: SMTP

## Quick Start

### Docker (recommended)

1. Copy the environment file and fill in your values:
   ```bash
   cp .env.example .env
   ```

2. Start the app:
   ```bash
   docker compose up -d
   ```

The app runs on `http://localhost:8000`. The SQLite database is persisted in `./data/`.

### Local Development

Requirements: Python 3.12+. The CI tests Python 3.12, 3.13, 3.14, and 3.15.

```bash
pip install -r requirements.txt
cp .env.example .env
# edit .env
uvicorn app.main:app --reload
```

## Environment Variables

| Variable | Description | Example |
|---|---|---|
| `ADMIN_USERNAME` | Admin panel username | `admin` |
| `ADMIN_PASSWORD` | Admin panel password | `changeme` |
| `SECRET_KEY` | Session secret key (random string) | `supersecretkey` |
| `BASE_URL` | Public base URL (used in emails) | `https://lootdrop.example.com` |
| `DATABASE_PATH` | Path to SQLite file | `/data/lootdrop.db` |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | SMTP username | `you@gmail.com` |
| `SMTP_PASSWORD` | SMTP password / app password | `yourpassword` |
| `SMTP_FROM_NAME` | Sender display name | `Lootdrop` |
| `SMTP_FROM_EMAIL` | Sender email address | `noreply@example.com` |
| `SMTP_USE_TLS` | Use STARTTLS (`true`/`false`) | `true` |
| `EMAIL_HOUR` | Default daily send hour (UTC) | `8` |
| `EMAIL_MINUTE` | Default daily send minute (UTC) | `0` |

## Admin Panel

Available at `/admin`. Log in with the credentials set in `ADMIN_USERNAME` / `ADMIN_PASSWORD`.

- **Dashboard**: live stats, trigger manual sync or email send, adjust sync interval and email send time
- **Giveaways**: browse and manage fetched giveaways
- **Subscribers**: add or remove subscribers manually

## Project Structure

```
app/
  main.py          # App entry point, scheduler setup
  models.py        # SQLModel database models
  i18n.py          # Translation strings (de/en)
  routes/
    admin.py       # Admin panel routes
    giveaways.py   # Public giveaway routes
    subscribe.py   # Subscribe / preferences / unsubscribe
  templates/
    base.html      # Public base layout
    index.html     # Home page with giveaway list
    subscribe.html # Subscribe form
    unsubscribe.html # Email preferences + unsubscribe
    admin/
      base.html    # Admin base layout
      dashboard.html
      giveaways.html
      subscribers.html
  static/
    favicon.svg
data/              # SQLite database (Docker volume)
docker-compose.yml
Dockerfile
.env.example
```
