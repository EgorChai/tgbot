from __future__ import annotations

import os
from datetime import date, timedelta
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv


@dataclass(frozen=True)
class Route:
    name: str
    origin: str
    destination: str
    dates: list[str]  # YYYY-MM-DD, one API query per date
    max_price: int
    max_transfers: int = 2
    one_way: bool = True
    priority: bool = False  # priority origins are checked and shown first


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


def _as_date(v) -> date:
    return v if isinstance(v, date) else date.fromisoformat(str(v))


def load_settings(config_path: str = "config.yaml") -> Settings:
    load_dotenv()
    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    routes = []
    for search in raw["searches"]:
        d = search["dates"]
        d_from, d_to = _as_date(d["from"]), _as_date(d["to"])
        dates = [(d_from + timedelta(days=i)).isoformat() for i in range((d_to - d_from).days + 1)]
        for o in search["origins"]:
            for dest in search["destinations"]:
                routes.append(
                    Route(
                        name=f"{o['name']} → {dest['name']}",
                        origin=o["code"].upper(),
                        destination=dest["code"].upper(),
                        dates=dates,
                        max_price=int(search["max_price"]),
                        max_transfers=int(search.get("max_transfers", 2)),
                        one_way=bool(search.get("one_way", True)),
                        priority=bool(o.get("priority", False)),
                    )
                )
    routes.sort(key=lambda r: not r.priority)  # stable: priority origins first
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
