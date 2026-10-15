from __future__ import annotations

import time
from pathlib import Path

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen (
    key TEXT PRIMARY KEY,
    price INTEGER NOT NULL,
    notified_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS state (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL
);
"""


class Storage:
    def __init__(self, path: str):
        self._path = path
        self._db: aiosqlite.Connection | None = None

    async def open(self) -> None:
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._path)
        await self._db.executescript(SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()

    async def should_notify(self, key: str, price: int, drop_percent: float) -> bool:
        """True for unseen tickets, or ones whose price fell enough since last alert."""
        async with self._db.execute("SELECT price FROM seen WHERE key=?", (key,)) as cur:
            row = await cur.fetchone()
        if row is None:
            return True
        return price <= row[0] * (1 - drop_percent / 100)

    async def mark_notified(self, key: str, price: int) -> None:
        await self._db.execute(
            "INSERT INTO seen(key, price, notified_at) VALUES(?,?,?) "
            "ON CONFLICT(key) DO UPDATE SET price=excluded.price, notified_at=excluded.notified_at",
            (key, price, time.time()),
        )
        await self._db.commit()

    async def set_state(self, k: str, v: str) -> None:
        await self._db.execute(
            "INSERT INTO state(k, v) VALUES(?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", (k, v)
        )
        await self._db.commit()

    async def get_state(self, k: str) -> str | None:
        async with self._db.execute("SELECT v FROM state WHERE k=?", (k,)) as cur:
            row = await cur.fetchone()
        return row[0] if row else None
