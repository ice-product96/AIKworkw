#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. Install Docker first." >&2
  exit 1
fi

if [[ ! -f .env.prod ]]; then
  echo "Create .env.prod from example:"
  echo "  cp .env.prod.example .env.prod"
  echo "Then edit POSTGRES_PASSWORD, JWT_SECRET, MINIO_ROOT_PASSWORD, CORS_ORIGINS"
  exit 1
fi

echo "Building and starting production stack..."
docker compose -f docker-compose.prod.yml --env-file .env.prod up --build -d

echo ""
echo "Stack is up. Configure host nginx (see docker/nginx-host.example.conf)."
echo "Frontend: http://127.0.0.1:$(grep -E '^FRONTEND_PORT=' .env.prod 2>/dev/null | cut -d= -f2 || echo 8011)"
echo "Admin: admin@example.com / password (change after first login)"
echo "Logs: docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f"
