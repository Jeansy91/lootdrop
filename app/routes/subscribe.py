import re
from typing import List

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from ..database import get_session
from ..i18n import get_lang, t
from ..models import Subscriber
from ..services.giveaway_service import PLATFORM_GROUPS, SYSTEM_GROUPS

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_ALL_GROUPS = sorted(SYSTEM_GROUPS.keys(), key=str.casefold)


def _ctx(request: Request, **kwargs):
    lang = get_lang(request)
    return {
        "request": request,
        "lang": lang,
        "t": lambda key: t(lang, key),
        "platform_groups": _ALL_GROUPS,
        **kwargs,
    }


@router.get("/subscribe", response_class=HTMLResponse)
async def subscribe_form(request: Request):
    return templates.TemplateResponse(
        "subscribe.html",
        _ctx(request, message=None, error=False, selected_platforms=_ALL_GROUPS),
    )


@router.post("/subscribe", response_class=HTMLResponse)
async def subscribe(
    request: Request,
    email: str = Form(...),
    language: str = Form("de"),
    platforms: List[str] = Form(default=[]),
    session: Session = Depends(get_session),
):
    lang = get_lang(request)

    if not _EMAIL_RE.match(email):
        return templates.TemplateResponse(
            "subscribe.html",
            _ctx(request, message=t(lang, "subscribe_invalid"),
                 error=True, selected_platforms=platforms or _ALL_GROUPS),
        )

    if session.exec(select(Subscriber).where(Subscriber.email == email)).first():
        return templates.TemplateResponse(
            "subscribe.html",
            _ctx(request, message=t(lang, "subscribe_exists"),
                 error=True, selected_platforms=platforms or _ALL_GROUPS),
        )

    chosen_lang = language if language in ("de", "en") else "de"
    # Leere Auswahl = alle Plattformen
    chosen_platforms = ",".join(g for g in platforms if g in _ALL_GROUPS)

    session.add(Subscriber(
        email=email,
        language=chosen_lang,
        subscriber_platforms=chosen_platforms,
    ))
    session.commit()

    return templates.TemplateResponse(
        "subscribe.html",
        _ctx(request, message=t(lang, "subscribe_success"),
             error=False, selected_platforms=platforms or _ALL_GROUPS),
    )


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(
    request: Request,
    token: str = None,
    session: Session = Depends(get_session),
):
    lang = get_lang(request)

    def _resp(success: bool):
        return templates.TemplateResponse(
            "unsubscribe.html",
            {"request": request, "lang": lang,
             "t": lambda key: t(lang, key), "success": success},
        )

    if not token:
        return _resp(False)

    subscriber = session.exec(
        select(Subscriber).where(Subscriber.token == token)
    ).first()

    if not subscriber:
        return _resp(False)

    subscriber.is_active = False
    session.add(subscriber)
    session.commit()
    return _resp(True)
