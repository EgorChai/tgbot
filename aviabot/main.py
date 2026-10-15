from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from .api import AviasalesClient
from .config import load_settings
from .storage import Storage
from .watcher import Watcher, format_ticket


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    s = load_settings()
    bot = Bot(s.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.message.filter(F.from_user.id.in_(s.admins))

    storage = Storage(s.db_path)
    await storage.open()
    client = AviasalesClient(s.api_token, s.currency, s.market, min_spacing=s.request_spacing)

    async def notify(route, ticket):
        text = format_ticket(route, ticket, s.marker)
        for chat_id in s.admins:
            await bot.send_message(chat_id, text, disable_web_page_preview=True)

    watcher = Watcher(s, client, storage, notify)

    @dp.message(Command("start"))
    async def start(m: Message):
        await m.answer("Слежу за билетами. /routes — направления, /check — проверить сейчас, /status")

    @dp.message(Command("routes"))
    async def routes(m: Message):
        await m.answer("\n".join(
            f"{'⭐' if r.priority else '•'} {r.name}: до {r.max_price} ₽, "
            f"пересадок ≤{r.max_transfers}, {r.dates[0]}…{r.dates[-1]}" for r in s.routes
        ))

    @dp.message(Command("check"))
    async def check(m: Message):
        await m.answer("Проверяю…")
        n = await watcher.check_all()
        await m.answer(f"Готово, новых уведомлений: {n}")

    @dp.message(Command("status"))
    async def status(m: Message):
        last = await storage.get_state("last_run") or "ещё не запускалось"
        await m.answer(f"Последняя проверка: {last}\nМинимальный цикл по лимиту API: {s.min_cycle_seconds:.0f} с")

    task = asyncio.create_task(watcher.run_forever())
    try:
        await dp.start_polling(bot)
    finally:
        task.cancel()
        await client.close()
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
