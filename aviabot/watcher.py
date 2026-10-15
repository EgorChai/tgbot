from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Awaitable, Callable

from .api import AviasalesClient, Ticket
from .config import Route, Settings
from .storage import Storage

log = logging.getLogger(__name__)

Notify = Callable[[Route, Ticket], Awaitable[None]]


def format_ticket(route: Route, t: Ticket, marker: str = "") -> str:
    dep = datetime.fromisoformat(t.departure_at).strftime("%d.%m.%Y %H:%M")
    lines = [
        f"{'⭐' if route.priority else '✈️'} <b>{route.name}</b> — <b>{t.price:,} ₽</b>".replace(",", " "),
        f"Вылет: {dep}",
    ]
    if t.return_at:
        lines.append(f"Обратно: {datetime.fromisoformat(t.return_at).strftime('%d.%m.%Y %H:%M')}")
    lines.append("Прямой" if t.transfers == 0 else f"Пересадок: {t.transfers}")
    if t.airline:
        lines.append(f"Авиакомпания: {t.airline}")
    lines.append(f'<a href="{t.url(marker)}">Открыть на Aviasales</a>')
    return "\n".join(lines)


class Watcher:
    def __init__(self, settings: Settings, client: AviasalesClient, storage: Storage, notify: Notify):
        self.s = settings
        self.client = client
        self.storage = storage
        self.notify = notify

    async def check_route(self, route: Route) -> int:
        found: list[Ticket] = []
        for day in route.dates:
            try:
                found += await self.client.search(route, day)
            except Exception:
                log.exception("search failed: %s %s", route.name, day)

        sent = 0
        for t in sorted(found, key=lambda t: (t.transfers, t.price)):  # fewer transfers first
            if await self.storage.should_notify(t.key, t.price, self.s.realert_drop_percent):
                await self.notify(route, t)
                await self.storage.mark_notified(t.key, t.price)
                sent += 1
        return sent

    async def check_all(self) -> int:
        total = 0
        for route in self.s.routes:
            total += await self.check_route(route)
        await self.storage.set_state("last_run", datetime.now().isoformat(timespec="seconds"))
        return total

    async def run_forever(self) -> None:
        interval = max(self.s.poll_interval_seconds, self.s.min_cycle_seconds)
        log.info("cycle interval: %.1fs (min allowed by rate limit: %.1fs)", interval, self.s.min_cycle_seconds)
        while True:
            started = time.monotonic()
            try:
                n = await self.check_all()
                log.info("cycle done, alerts sent: %d", n)
            except Exception:
                log.exception("cycle failed")
            await asyncio.sleep(max(0.0, interval - (time.monotonic() - started)))
