# aviabot

Следит за ценами Aviasales по заданным направлениям и шлёт уведомление в Telegram,
когда находится билет дешевле порога. Данные берутся из официального
Travelpayouts Data API (кэш цен Aviasales) — без парсинга сайта и капч.

## Запуск
1. Токен API: https://www.travelpayouts.com/developers/api (нужна регистрация в партнёрке).
2. `cp .env.example .env` и `cp config.example.yaml config.yaml`, заполнить.
3. Локально: `pip install -r requirements.txt && python -m aviabot.main`.
4. На VPS (Linux, Python 3.10+): `sudo ./deploy/install.sh`, заполнить `/opt/aviabot/.env` и `config.yaml`,
   затем `systemctl restart aviabot`. Логи: `journalctl -u aviabot -f`.

Команды бота (только для `ADMINS`): `/routes`, `/check`, `/status`.
Тесты: `pytest`.
