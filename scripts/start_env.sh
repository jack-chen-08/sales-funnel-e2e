#!/usr/bin/env bash
# 起环境：PostgreSQL 16（docker compose）→ Alembic 建表 → 启动 mock 平台（5600 端口）
set -euo pipefail
cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "缺少 .env，请先复制 .env.example 为 .env 并填写数据库口令"
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

echo "== 1/3 启动 PostgreSQL 16 =="
docker compose --env-file .env up -d
for _ in $(seq 1 30); do
  status=$(docker inspect -f '{{.State.Health.Status}}' smoke-pg 2>/dev/null || echo starting)
  [[ "$status" == "healthy" ]] && break
  sleep 1
done
docker exec smoke-pg psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc "select version();" | head -1

echo "== 2/3 Alembic 迁移 =="
.venv/bin/alembic upgrade head

echo "== 3/3 启动 mock 平台 http://127.0.0.1:${SMOKE_PLATFORM_PORT:-5600} =="
if [[ -f .platform.pid ]] && kill -0 "$(cat .platform.pid)" 2>/dev/null; then
  echo "平台已在运行（pid $(cat .platform.pid)）"
else
  .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port "${SMOKE_PLATFORM_PORT:-5600}" \
    > reports/platform.log 2>&1 &
  echo $! > .platform.pid
  for _ in $(seq 1 30); do
    curl -sf "http://127.0.0.1:${SMOKE_PLATFORM_PORT:-5600}/healthz" >/dev/null && break
    sleep 1
  done
fi
curl -s "http://127.0.0.1:${SMOKE_PLATFORM_PORT:-5600}/healthz"
echo
echo "环境就绪。"
