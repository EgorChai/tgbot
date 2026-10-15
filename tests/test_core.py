import httpx
import pytest

from aviabot.api import AviasalesClient
from aviabot.config import Route
from aviabot.storage import Storage

ROUTE = Route("t", "DAD", "MOW", ["2026-10-29"], max_price=35000, max_transfers=1)


def _item(price, transfers, dep, ret):
    return {"origin": "MOW", "destination": "IST", "price": price, "transfers": transfers,
            "departure_at": dep, "return_at": ret, "airline": "TK", "link": "/search/X"}


async def test_search_filters():
    data = [
        _item(30000, 1, "2026-10-29T10:00:00+07:00", None),  # ok
        _item(40000, 0, "2026-10-29T10:00:00+07:00", None),  # too expensive
        _item(20000, 2, "2026-10-29T10:00:00+07:00", None),  # too many transfers
        _item(20000, 0, "2026-10-30T10:00:00+07:00", None),  # other day
    ]
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"success": True, "data": data}))
    c = AviasalesClient("tok", client=httpx.AsyncClient(transport=transport, base_url="https://x"))
    res = await c.search(ROUTE, "2026-10-29")
    assert [t.price for t in res] == [30000]
    assert res[0].url("m1").endswith("?marker=m1")


def test_config_expands_routes(tmp_path, monkeypatch):
    from aviabot.config import load_settings
    monkeypatch.setenv("BOT_TOKEN", "x"); monkeypatch.setenv("TRAVELPAYOUTS_TOKEN", "y")
    monkeypatch.setenv("ADMINS", "1")
    s = load_settings("config.example.yaml")
    assert len(s.routes) == 4 * 2 + 4
    assert s.routes[0].origin == "DAD" and s.routes[0].priority
    ovb = [r for r in s.routes if r.destination == "OVB"]
    assert all(r.max_transfers == 0 and r.max_price == 20000 for r in ovb)
    assert s.routes[0].dates == ["2026-10-29", "2026-10-30", "2026-10-31"]


async def test_dedup_and_price_drop():
    st = Storage(":memory:")
    await st.open()
    assert await st.should_notify("k", 1000, 5)
    await st.mark_notified("k", 1000)
    assert not await st.should_notify("k", 1000, 5)
    assert not await st.should_notify("k", 980, 5)
    assert await st.should_notify("k", 940, 5)
    await st.close()


def test_rate_limit_margin(monkeypatch):
    from aviabot.config import load_settings
    monkeypatch.setenv("BOT_TOKEN", "x"); monkeypatch.setenv("TRAVELPAYOUTS_TOKEN", "y")
    s = load_settings("config.example.yaml")
    assert 60 / s.request_spacing == pytest.approx(510)
    assert s.min_cycle_seconds == pytest.approx(36 * 60 / 510)


async def test_throttle_spacing():
    import time
    c = AviasalesClient("t", client=httpx.AsyncClient(base_url="https://x"), min_spacing=0.05)
    t0 = time.monotonic()
    for _ in range(5):
        await c._throttle()
    assert time.monotonic() - t0 >= 0.19
