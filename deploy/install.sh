#!/usr/bin/env bash
# Run on the VPS from the repo root: sudo ./deploy/install.sh
set -euo pipefail
APP=/opt/aviabot
mkdir -p "$APP"
cp -r aviabot requirements.txt "$APP"/
[ -f "$APP/.env" ] || cp .env.example "$APP/.env"
[ -f "$APP/config.yaml" ] || cp config.example.yaml "$APP/config.yaml"
python3 -m venv "$APP/.venv"
"$APP/.venv/bin/pip" install -q -r requirements.txt
cp deploy/aviabot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable aviabot
echo "Fill $APP/.env and $APP/config.yaml, then: systemctl restart aviabot && journalctl -u aviabot -f"
