from sqlmodel import Session

from ..config import settings as env_settings
from ..models import AppSetting

SYNC_INTERVAL_KEY = "sync_interval_minutes"
EMAIL_HOUR_KEY    = "email_hour"
EMAIL_MINUTE_KEY  = "email_minute"

_DEFAULTS = {
    SYNC_INTERVAL_KEY: str(5),
    EMAIL_HOUR_KEY:    str(env_settings.email_hour),
    EMAIL_MINUTE_KEY:  str(env_settings.email_minute),
}


def get_setting(session: Session, key: str) -> str:
    row = session.get(AppSetting, key)
    return row.value if row else _DEFAULTS[key]


def set_setting(session: Session, key: str, value: str) -> None:
    row = session.get(AppSetting, key)
    if row:
        row.value = value
    else:
        row = AppSetting(key=key, value=value)
    session.add(row)
    session.commit()


def get_sync_interval(session: Session) -> int:
    return int(get_setting(session, SYNC_INTERVAL_KEY))


def get_email_time(session: Session) -> tuple[int, int]:
    hour   = int(get_setting(session, EMAIL_HOUR_KEY))
    minute = int(get_setting(session, EMAIL_MINUTE_KEY))
    return hour, minute
