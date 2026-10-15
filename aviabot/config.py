from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class Route:
    name: str
    origin: str
    destination: str
    months: list[str]
    max_price: int
    one_way: bool = False
    direct_only: bool = False
    stay_days: tuple[int, int] | None = None  # (min, max) for round trips


@dataclass(frozen=True)
class Settings:
    bot_token: str
    api_token: str
    admins: list[int]
    marker: str
    routes: list[Route]
    poll_interval_minutes: int = 30
    currency: str = "rub"
    market: str = "ru"
    realert_drop_percent: float = 5.0
    db_path: str = "data/aviabot.db"


def load_settings(config_path: str = "config.yaml") -> Settings:
    load_dotenv()
    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    routes = []
    for r in raw["routes"]:
        stay = r.get("stay_days")
        routes.append(
            Route(
                name=r.get("name") or f"{r['origin']} → {r['destination']}",
                origin=r["origin"].upper(),
                destination=r["destination"].upper(),
                months=[str(m) for m in r["months"]],
                max_price=int(r["max_price"]),
                one_way=bool(r.get("one_way", False)),
                direct_only=bool(r.get("direct_only", False)),
                stay_days=tuple(stay) if stay else None,
            )
        )
    return Settings(
        bot_token=os.environ["BOT_TOKEN"],
        api_token=os.environ["TRAVELPAYOUTS_TOKEN"],
        admins=[int(x) for x in os.environ.get("ADMINS", "").split(",") if x.strip()],
        marker=os.environ.get("TRAVELPAYOUTS_MARKER", ""),
        routes=routes,
        poll_interval_minutes=int(raw.get("poll_interval_minutes", 30)),
        currency=raw.get("currency", "rub"),
        market=raw.get("market", "ru"),
        realert_drop_percent=float(raw.get("realert_drop_percent", 5)),
        db_path=os.environ.get("DB_PATH", "data/aviabot.db"),
    )
