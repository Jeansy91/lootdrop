import logging
import re
from typing import List

from sqlmodel import Session, select

from ..models import Giveaway
from .gamerpower import fetch_giveaways

log = logging.getLogger(__name__)

# ── Plattform-Dimensionen ─────────────────────────────────────────────────────

# Spieleplattform: auf welchem System wird gespielt
SYSTEM_GROUPS: dict[str, list[str]] = {
    "PC":              ["Steam", "Epic Games Store", "GOG", "Ubisoft Connect", "PC", "itch.io", "IndieGala"],
    "PS5":             ["PS5"],
    "PS4":             ["PS4"],
    "Xbox Series X/S": ["Xbox Series X/S"],
    "Xbox One":        ["Xbox One"],
    "Nintendo Switch": ["Nintendo Switch"],
    "Android":         ["Android"],
    "iOS":             ["iOS"],
    "VR":              ["VR"],
}

# Store/Download-Plattform: wo wird es bezogen
STORE_GROUPS: dict[str, list[str]] = {
    "Steam":            ["Steam"],
    "Epic Games Store": ["Epic Games Store"],
    "GOG":              ["GOG"],
    "Ubisoft Connect":  ["Ubisoft Connect"],
    "itch.io":          ["itch.io"],
    "IndieGala":        ["IndieGala"],
    "PlayStation Store":["PS5", "PS4"],
    "Xbox Store":       ["Xbox Series X/S", "Xbox One"],
    "Nintendo eShop":   ["Nintendo Switch"],
    "Google Play":      ["Android"],
    "App Store":        ["iOS"],
    "Stove":            ["Stove"],
}

# Für E-Mail-Subscriber-Filterung (Systemgruppen)
PLATFORM_GROUPS = SYSTEM_GROUPS

# Reihenfolge der Badges: System-/Geräteplattformen zuerst, dann Stores
_PLATFORM_ORDER: list[str] = [
    # System / Gerät
    "PC", "PS5", "PS4", "Xbox Series X/S", "Xbox One",
    "Nintendo Switch", "Android", "iOS", "VR",
    # Store / Download-Plattform
    "Steam", "Epic Games Store", "GOG", "Ubisoft Connect",
    "itch.io", "IndieGala", "Stove",
]

_PLATFORM_MAP: dict[str, str] = {
    # PC
    "steam":                 "Steam",
    "epic games store":      "Epic Games Store",
    "epic games":            "Epic Games Store",
    "epic":                  "Epic Games Store",
    "gog":                   "GOG",
    "gog.com":               "GOG",
    "ubisoft connect":       "Ubisoft Connect",
    "ubisoft":               "Ubisoft Connect",
    "pc":                    "PC",
    "drm-free":              "PC",
    "drm free":              "PC",
    "itch.io":               "itch.io",
    "itch":                  "itch.io",
    "indiegala":             "IndieGala",
    # PlayStation
    "ps5":                   "PS5",
    "playstation 5":         "PS5",
    "ps4":                   "PS4",
    "playstation 4":         "PS4",
    "playstation":           "PS4",
    # Xbox
    "xbox series xs":        "Xbox Series X/S",
    "xbox series x/s":       "Xbox Series X/S",
    "xbox series x":         "Xbox Series X/S",
    "xbox one":              "Xbox One",
    "xbox":                  "Xbox One",
    # Nintendo
    "switch":                "Nintendo Switch",
    "nintendo switch":       "Nintendo Switch",
    # Mobile
    "android":               "Android",
    "ios":                   "iOS",
    "iphone":                "iOS",
    "ipad":                  "iOS",
    # VR
    "vr":                    "VR",
    "oculus":                "VR",
    "oculus rift":           "VR",
    "rift":                  "VR",
    "meta quest":            "VR",
    # Mobile (generisch)
    "mobile":                "Android",   # wird als Android gewertet
    # Weitere Stores
    "stove":                 "Stove",
}

_PLATFORM_DETECT = re.compile(
    r"^(steam|epic games? store|epic games?|epic|gog(?:\.com)?|"
    r"ubisoft(?: connect)?|drm.?free|itch\.?io|indiegala|"
    r"ps5|playstation ?5|ps4|playstation ?4|playstation|"
    r"xbox series x[/s]*|xbox one|xbox|"
    r"nintendo switch|switch|"
    r"android|ios|iphone|ipad|mobile|"
    r"vr|oculus(?: rift)?|rift|meta quest|"
    r"stove)$",
    re.IGNORECASE,
)


def _normalize(raw: str) -> str | None:
    return _PLATFORM_MAP.get(raw.strip().lower())


def _is_platform_content(text: str) -> bool:
    return all(
        _PLATFORM_DETECT.fullmatch(p.strip())
        for p in text.split(",") if p.strip()
    )


def extract_platforms(api_platforms: str, raw_title: str) -> list[str]:
    found: set[str] = set()
    for p in api_platforms.split(","):
        n = _normalize(p.strip())
        if n:
            found.add(n)
    for m in re.finditer(r"\(([^)]+)\)", raw_title):
        for part in m.group(1).split(","):
            n = _normalize(part.strip())
            if n:
                found.add(n)
    return sorted(found, key=lambda x: (
        _PLATFORM_ORDER.index(x) if x in _PLATFORM_ORDER else 99,
        x,
    ))


# ── Titel-Bereinigung ─────────────────────────────────────────────────────────

_CLAIM_PREFIX    = re.compile(r"^(Claim|Get|Grab|Download)\s+", re.IGNORECASE)
_FOR_FREE_SUFFIX = re.compile(r"\s+for\s+Free\s*$", re.IGNORECASE)
_TRAILING_NOISE  = re.compile(r"\s*[-–|:]\s*(Free\b.*|Giveaway|PC Game)\s*$", re.IGNORECASE)
_GIVEAWAY_SUFFIX = re.compile(r"\s+Giveaway\s*$", re.IGNORECASE)


def clean_title(raw: str) -> str:
    t = raw.strip()
    t = _CLAIM_PREFIX.sub("", t)
    t = _FOR_FREE_SUFFIX.sub("", t)
    t = _TRAILING_NOISE.sub("", t)
    t = _GIVEAWAY_SUFFIX.sub("", t)
    while True:
        m = re.search(r"\s*\(([^)]+)\)\s*$", t)
        if m and _is_platform_content(m.group(1)):
            t = t[: m.start()].strip()
        else:
            break
    return t.strip()


# ── Sync ──────────────────────────────────────────────────────────────────────

async def sync_giveaways(session: Session) -> List[Giveaway]:
    raw = await fetch_giveaways()
    new_giveaways: List[Giveaway] = []

    for item in raw:
        raw_title    = item.get("title", "")
        api_platforms = item.get("platforms", "")
        title        = clean_title(raw_title)
        platforms    = ", ".join(extract_platforms(api_platforms, raw_title))

        existing = session.get(Giveaway, item["id"])
        if existing:
            existing.status       = item.get("status", "Active")
            existing.title        = title
            existing.platforms    = platforms
            existing.instructions = item.get("instructions")
            session.add(existing)
        else:
            giveaway = Giveaway(
                id=item["id"],
                title=title,
                worth=item.get("worth"),
                thumbnail=item.get("thumbnail"),
                image=item.get("image"),
                description=item.get("description"),
                instructions=item.get("instructions"),
                open_giveaway_url=item.get("open_giveaway_url"),
                published_date=item.get("published_date"),
                type=item.get("type", "game"),
                platforms=platforms,
                end_date=item.get("end_date"),
                status=item.get("status", "Active"),
                email_sent=False,
            )
            session.add(giveaway)
            new_giveaways.append(giveaway)
            log.info("New giveaway: %s [%s] (id=%d)", title, platforms, giveaway.id)

    session.commit()
    log.info("Sync complete: %d new, %d total fetched", len(new_giveaways), len(raw))
    return new_giveaways


def get_active_giveaways(session: Session) -> List[Giveaway]:
    return list(
        session.exec(
            select(Giveaway)
            .where(Giveaway.status == "Active")
            .order_by(Giveaway.id.desc())
        ).all()
    )


def get_unsent_giveaways(session: Session) -> List[Giveaway]:
    return list(
        session.exec(
            select(Giveaway).where(
                Giveaway.status == "Active", Giveaway.email_sent == False
            )
        ).all()
    )


def mark_as_sent(session: Session, giveaways: List[Giveaway]) -> None:
    for g in giveaways:
        g.email_sent = True
        session.add(g)
    session.commit()
