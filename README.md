# aviabot

Следит за ценами Aviasales по заданным направлениям и шлёт уведомление в Telegram,
когда находится билет дешевле порога. Данные берутся из официального
Travelpayouts Data API (кэш цен Aviasales) — без парсинга сайта и капч.

## Запуск
1. Токен API: https://www.travelpayouts.com/developers/api (нужна регистрация в партнёрке).
2. `cp .env.example .env` и `cp config.example.yaml config.yaml`, заполнить.
3. `docker compose up -d --build` (или `pip install -r requirements.txt && python -m aviabot.main`).

Команды бота (только для `ADMINS`): `/routes`, `/check`, `/status`.
Тесты: `pytest`.
