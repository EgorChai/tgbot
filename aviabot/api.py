"""Client for the Travelpayouts / Aviasales Data API (cached prices, no captcha)."""
from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from .config import Route

log = logging.getLogger(__name__)

BASE_URL = "https://api.travelpayouts.com"
SITE_URL = "https://www.aviasales.ru"


@dataclass(frozen=True)
class Ticket:
    origin: str
    destination: str
    price: int
    departure_at: str
    return_at: str | None
    transfers: int
    airline: str
    duration: int | None
    link: str  # relative aviasales link

    @property
    def key(self) -> str:
        return f"{self.origin}-{self.destination}|{self.departure_at}|{self.return_at or ''}|{self.transfers}"

    def url(self, marker: str = "") -> str:
        url = SITE_URL + self.link
        if marker:
            url += ("&" if "?" in url else "?") + f"marker={marker}"
        return url


class AviasalesClient:
    def __init__(self, token: str, currency: str = "rub", market: str = "ru",
                 client: httpx.AsyncClient | None = None):
        self._currency = currency
        self._market = market
        self._client = client or httpx.AsyncClient(
            base_url=BASE_URL,
            headers={"X-Access-Token": token},
            timeout=20,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def search(self, route: Route, day: str) -> list[Ticket]:
        params: dict = {
            "origin": route.origin,
            "destination": route.destination,
            "departure_at": day,
            "one_way": str(route.one_way).lower(),
            "direct": str(route.max_transfers == 0).lower(),
            "currency": self._currency,
            "market": self._market,
            "sorting": "price",
            "unique": "false",
            "limit": 50,
        }
        resp = await self._client.get("/aviasales/v3/prices_for_dates", params=params)
        resp.raise_for_status()
        payload = resp.json()
        if not payload.get("success", True):
            raise RuntimeError(f"API error: {payload.get('error')}")

        tickets = []
        for item in payload.get("data", []):
            t = Ticket(
                origin=item.get("origin", route.origin),
                destination=item.get("destination", route.destination),
                price=int(item["price"]),
                departure_at=item["departure_at"],
                return_at=item.get("return_at"),
                transfers=int(item.get("transfers", item.get("number_of_changes", 0)) or 0),
                airline=item.get("airline", ""),
                duration=item.get("duration"),
                link=item.get("link", ""),
            )
            if _matches(route, t, day):
                tickets.append(t)
        return tickets


def _matches(route: Route, t: Ticket, day: str) -> bool:
    return (
        t.price <= route.max_price
        and t.transfers <= route.max_transfers
        and t.departure_at.startswith(day)
    )
