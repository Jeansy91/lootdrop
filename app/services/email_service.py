import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import List

from jinja2 import Environment, FileSystemLoader

from ..config import settings
from ..models import Giveaway, Subscriber
from .giveaway_service import PLATFORM_GROUPS

log = logging.getLogger(__name__)

_template_dir = Path(__file__).parent.parent / "templates"
_jinja = Environment(loader=FileSystemLoader(str(_template_dir)), autoescape=True)

_SUBJECTS = {
    "de": "Lootdrop – Neue kostenlose Spiele heute",
    "en": "Lootdrop – New free games today",
}


def _render(giveaways: List[Giveaway], subscriber: Subscriber, base_url: str) -> str:
    lang = subscriber.language if subscriber.language in ("de", "en") else "de"
    template = _jinja.get_template(f"email/daily_{lang}.html")
    return template.render(
        giveaways=giveaways,
        base_url=base_url.rstrip('/'),
        unsubscribe_url=f"{base_url.rstrip('/')}/unsubscribe?token={subscriber.token}",
    )


def _send(to: str, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.sendmail(settings.smtp_from_email, to, msg.as_string())


def _filter_for_subscriber(
    giveaways: List[Giveaway], subscriber: Subscriber
) -> List[Giveaway]:
    """Return only giveaways matching the subscriber's platform preferences.
    Empty subscriber_platforms means all platforms."""
    if not subscriber.subscriber_platforms:
        return giveaways

    selected_groups = [g.strip() for g in subscriber.subscriber_platforms.split(",") if g.strip()]
    allowed: set[str] = set()
    for group in selected_groups:
        allowed.update(PLATFORM_GROUPS.get(group, []))

    return [
        g for g in giveaways
        if allowed & {p.strip() for p in g.platforms.split(",") if p.strip()}
    ]


def send_daily_emails(
    giveaways: List[Giveaway],
    subscribers: List[Subscriber],
    base_url: str,
) -> None:
    if not giveaways or not subscribers:
        return

    sent = 0
    for subscriber in subscribers:
        if not subscriber.is_active:
            continue
        filtered = _filter_for_subscriber(giveaways, subscriber)
        if not filtered:
            continue
        lang = subscriber.language if subscriber.language in ("de", "en") else "de"
        try:
            html = _render(filtered, subscriber, base_url)
            _send(subscriber.email, _SUBJECTS[lang], html)
            sent += 1
        except Exception as exc:
            log.error("Failed to send email to %s: %s", subscriber.email, exc)

    log.info("Sent emails to %d/%d subscribers", sent, len(subscribers))
