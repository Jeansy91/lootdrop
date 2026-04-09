import secrets
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AppSetting(SQLModel, table=True):
    __tablename__ = "app_setting"
    key: str = Field(primary_key=True)
    value: str


class Giveaway(SQLModel, table=True):
    id: int = Field(primary_key=True)          # GamerPower-ID
    title: str
    worth: Optional[str] = None                # z.B. "$14.99"
    thumbnail: Optional[str] = None
    image: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    open_giveaway_url: Optional[str] = None    # Direktlink zur Plattform
    published_date: Optional[str] = None
    type: str = "game"
    platforms: str = ""                        # z.B. "Steam, Epic Games Store"
    end_date: Optional[str] = None             # "N/A" oder Datum
    status: str = "Active"
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    email_sent: bool = Field(default=False)


class Subscriber(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    language: str = Field(default="de")        # "de" oder "en"
    token: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    # Kommaseparierte Plattform-Gruppen; leer = alle Gruppen
    subscriber_platforms: str = Field(default="")
