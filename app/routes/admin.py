from typing import List

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from ..config import settings
from ..database import get_session
from ..i18n import get_lang, t
from ..models import Giveaway, Subscriber
from ..scheduler import reschedule_email, reschedule_sync
from ..services.email_service import send_daily_emails
from ..services.giveaway_service import (
    PLATFORM_GROUPS,
    get_active_giveaways,
    get_unsent_giveaways,
    mark_as_sent,
    sync_giveaways,
)
from ..services.settings_service import (
    EMAIL_HOUR_KEY,
    EMAIL_MINUTE_KEY,
    SYNC_INTERVAL_KEY,
    get_email_time,
    get_sync_interval,
    set_setting,
)

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="app/templates")


def _require_admin(request: Request):
    """Redirect to login if not authenticated."""
    return request.session.get("admin") is True


def _ctx(request: Request, **kwargs):
    lang = get_lang(request)
    return {"request": request, "lang": lang, "t": lambda key: t(lang, key), **kwargs}


# ── Auth ──────────────────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def admin_root():
    return RedirectResponse(url="/admin/dashboard")


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse(
        "admin/login.html", _ctx(request, error=None)
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    if username == settings.admin_username and password == settings.admin_password:
        request.session["admin"] = True
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    lang = get_lang(request)
    return templates.TemplateResponse(
        "admin/login.html",
        _ctx(request, error=t(lang, "admin_wrong_credentials")),
    )


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/admin/login")


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: Session = Depends(get_session)):
    if not _require_admin(request):
        return RedirectResponse(url="/admin/login")
    message = request.session.pop("message", None)
    hour, minute = get_email_time(session)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        _ctx(
            request,
            giveaway_count=len(get_active_giveaways(session)),
            subscriber_count=len(session.exec(
                select(Subscriber).where(Subscriber.is_active == True)
            ).all()),
            sync_interval=get_sync_interval(session),
            email_hour=hour,
            email_minute=minute,
            message=message,
        ),
    )


@router.post("/settings")
async def save_settings(
    request: Request,
    sync_interval: int = Form(...),
    email_hour: int = Form(...),
    email_minute: int = Form(...),
    session: Session = Depends(get_session),
):
    if not _require_admin(request):
        return RedirectResponse(url="/admin/login")

    sync_interval = max(1, min(1440, sync_interval))
    email_hour    = max(0, min(23, email_hour))
    email_minute  = max(0, min(59, email_minute))

    set_setting(session, SYNC_INTERVAL_KEY, str(sync_interval))
    set_setting(session, EMAIL_HOUR_KEY,    str(email_hour))
    set_setting(session, EMAIL_MINUTE_KEY,  str(email_minute))

    reschedule_sync(sync_interval)
    reschedule_email(email_hour, email_minute)

    lang = get_lang(request)
    request.session["message"] = t(lang, "admin_settings_saved")
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.post("/refresh")
async def refresh_giveaways(request: Request, session: Session = Depends(get_session)):
    if not _require_admin(request):
        return RedirectResponse(url="/admin/login")
    await sync_giveaways(session)
    lang = get_lang(request)
    request.session["message"] = t(lang, "refreshed")
    return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.post("/send-email")
async def send_email_now(request: Request, session: Session = Depends(get_session)):
    if not _require_admin(request):
        return RedirectResponse(url="/admin/login")
    unsent = get_unsent_giveaways(session)
    subscribers = list(
        session.exec(select(Subscriber).where(Subscriber.is_active == True)).all()
    )
    base_url = str(request.base_url).rstrip("/")
    send_daily_emails(unsent, subscribers, base_url)
    mark_as_sent(session, unsent)
    lang = get_lang(request)
    request.session["message"] = t(lang, "admin_trigger_success")
    return RedirectResponse(url="/admin/dashboard", status_code=303)


# ── Subscribers ───────────────────────────────────────────────────────────────

@router.get("/subscribers", response_class=HTMLResponse)
async def subscribers_list(request: Request, session: Session = Depends(get_session)):
    if not _require_admin(request):
        return RedirectResponse(url="/admin/login")
    message = request.session.pop("message", None)
    subscribers = list(
        session.exec(select(Subscriber).order_by(Subscriber.created_at.desc())).all()
    )
    return templates.TemplateResponse(
        "admin/subscribers.html",
        _ctx(request, subscribers=subscribers, message=message,
             platform_groups=list(PLATFORM_GROUPS.keys())),
    )


@router.post("/subscribers/add")
async def add_subscriber(
    request: Request,
    email: str = Form(...),
    language: str = Form("de"),
    platforms: List[str] = Form(default=[]),
    session: Session = Depends(get_session),
):
    if not _require_admin(request):
        return RedirectResponse(url="/admin/login")
    if not session.exec(select(Subscriber).where(Subscriber.email == email)).first():
        lang = language if language in ("de", "en") else "de"
        chosen_platforms = ",".join(g for g in platforms if g in PLATFORM_GROUPS)
        session.add(Subscriber(email=email, language=lang, subscriber_platforms=chosen_platforms))
        session.commit()
    return RedirectResponse(url="/admin/subscribers", status_code=303)


@router.post("/subscribers/{sub_id}/delete")
async def delete_subscriber(
    request: Request,
    sub_id: int,
    session: Session = Depends(get_session),
):
    if not _require_admin(request):
        return RedirectResponse(url="/admin/login")
    subscriber = session.get(Subscriber, sub_id)
    if subscriber:
        session.delete(subscriber)
        session.commit()
    return RedirectResponse(url="/admin/subscribers", status_code=303)
