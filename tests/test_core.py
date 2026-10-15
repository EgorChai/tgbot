import httpx
import pytest

from aviabot.api import AviasalesClient
from aviabot.config import Route
from aviabot.storage import Storage

ROUTE = Route("t", "MOW", "IST", ["2026-12"], max_price=10000, direct_only=True, stay_days=(5, 10))


def _item(price, transfers, dep, ret):
    return {"origin": "MOW", "destination": "IST", "price": price, "transfers": transfers,
            "departure_at": dep, "return_at": ret, "airline": "TK", "link": "/search/X"}


async def test_search_filters():
    data = [
        _item(9000, 0, "2026-12-01T10:00:00+03:00", "2026-12-07T10:00:00+03:00"),  # ok
        _item(12000, 0, "2026-12-01T10:00:00+03:00", "2026-12-07T10:00:00+03:00"),  # too expensive
        _item(8000, 1, "2026-12-01T10:00:00+03:00", "2026-12-07T10:00:00+03:00"),  # transfer
        _item(8000, 0, "2026-12-01T10:00:00+03:00", "2026-12-20T10:00:00+03:00"),  # stay too long
    ]
    transport = httpx.MockTransport(lambda r: httpx.Response(200, json={"success": True, "data": data}))
    c = AviasalesClient("tok", client=httpx.AsyncClient(transport=transport, base_url="https://x"))
    res = await c.search(ROUTE, "2026-12")
    assert [t.price for t in res] == [9000]
    assert res[0].url("m1").endswith("?marker=m1")


async def test_dedup_and_price_drop():
    st = Storage(":memory:")
    await st.open()
    assert await st.should_notify("k", 1000, 5)
    await st.mark_notified("k", 1000)
    assert not await st.should_notify("k", 1000, 5)
    assert not await st.should_notify("k", 980, 5)
    assert await st.should_notify("k", 940, 5)
    await st.close()
