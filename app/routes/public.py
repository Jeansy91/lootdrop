import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from ..database import get_session
from ..i18n import get_lang, t
from ..services.giveaway_service import STORE_GROUPS, SYSTEM_GROUPS, get_active_giveaways

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    lang: str = None,
    session: Session = Depends(get_session),
):
    current_lang = lang if lang in ("de", "en") else get_lang(request)
    ctx = {
        "request": request,
        "giveaways": get_active_giveaways(session),
        "system_groups": sorted(SYSTEM_GROUPS.keys(), key=str.casefold),
        "store_groups": sorted(STORE_GROUPS.keys(), key=str.casefold),
        "system_groups_json": json.dumps(SYSTEM_GROUPS),
        "store_groups_json": json.dumps(STORE_GROUPS),
        "lang": current_lang,
        "t": lambda key: t(current_lang, key),
    }
    response = templates.TemplateResponse(
        request=request,
        name="index.html",
        context=ctx,
    )
    if lang in ("de", "en"):
        response.set_cookie("lang", lang, max_age=60 * 60 * 24 * 365, httponly=True)
    return response
