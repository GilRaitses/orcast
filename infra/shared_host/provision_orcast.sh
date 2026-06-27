#!/usr/bin/env bash
# Provision the orcast FastAPI backend as a CO-TENANT on the shared self-host
# (the pax aimez-services EC2). Idempotent. Run ON the host as a sudo-capable
# user. Additive only: it never touches the pax infer/shade services, the pax
# venv, or the cloudflared tunnel ingress.
#
# Prereqs (outside this script):
#   - the shared host is already provisioned for pax (cloudflared tunnel active)
#   - the orcast service env file is injected out-of-band AFTER this runs:
#       /opt/orcast/infra/shared_host/env/orcast-services.env  (chmod 600)
#   - the cloudflared ingress + DNS for orcast-api.aimez.ai are added via the
#     Cloudflare API (see cloudflared/orcast-ingress.md)
set -euo pipefail

ORCAST_REPO="${ORCAST_REPO:-https://github.com/GilRaitses/orcast.git}"
ORCAST_DIR="/opt/orcast"
# orcast's backend uses PEP 701 f-strings (e.g. routers/review_dossier.py), so it
# requires Python 3.12+ (matches tools/deployment/aws/Dockerfile python:3.12-slim).
PY="${PY:-python3.12}"

echo "[provision] system packages (python3.12 via deadsnakes; additive, pax venv untouched)"
sudo apt-get update -y
sudo apt-get install -y software-properties-common git build-essential libpq-dev
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -y
sudo apt-get install -y "${PY}" "${PY}-venv" "${PY}-dev"

echo "[provision] service user + checkout"
id orcast >/dev/null 2>&1 || sudo useradd -r -d "$ORCAST_DIR" -s /usr/sbin/nologin orcast
if [ ! -d "$ORCAST_DIR/.git" ]; then
  sudo rm -rf "$ORCAST_DIR"
  sudo git clone --depth 1 "$ORCAST_REPO" "$ORCAST_DIR"
else
  sudo git config --global --add safe.directory "$ORCAST_DIR"
  sudo git -C "$ORCAST_DIR" pull --ff-only
fi
sudo chown -R orcast:orcast "$ORCAST_DIR"

echo "[provision] venv + deps"
sudo -u orcast "$PY" -m venv "$ORCAST_DIR/venv"
sudo -u orcast "$ORCAST_DIR/venv/bin/pip" install --upgrade pip
sudo -u orcast "$ORCAST_DIR/venv/bin/pip" install -r "$ORCAST_DIR/tools/deployment/aws/requirements.txt"

echo "[provision] env file placeholder (real values injected out-of-band)"
ENVF="$ORCAST_DIR/infra/shared_host/env/orcast-services.env"
if [ ! -f "$ENVF" ]; then
  sudo mkdir -p "$ORCAST_DIR/infra/shared_host/env"
  sudo cp "$ORCAST_DIR/infra/shared_host/env/orcast-services.env.example" "$ENVF"
  sudo chown orcast:orcast "$ENVF"; sudo chmod 600 "$ENVF"
  echo "[provision] NOTE: $ENVF is a placeholder; inject secrets (ORCAST_API_KEY, ORCAST_DB_PASSWORD) before starting."
fi

echo "[provision] preflight (fail-fast before starting service)"
sudo -u orcast bash -c "set -a; . '$ENVF'; set +a; ORCAST_DIR='$ORCAST_DIR' '$ORCAST_DIR/venv/bin/python' '$ORCAST_DIR/infra/shared_host/preflight.py'" || {
  echo "[provision] PREFLIGHT FAILED — refusing to start orcast-api. Fix the issues above."; exit 1; }

echo "[provision] systemd unit"
sudo cp "$ORCAST_DIR/infra/shared_host/systemd/orcast-api.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now orcast-api.service

echo "[provision] health"
sleep 3
curl -fsS http://127.0.0.1:8090/health && echo
echo "[provision] done. Next: ensure the cloudflared ingress + DNS for orcast-api.aimez.ai are live, then set Vercel ORCAST_API_BASE."
