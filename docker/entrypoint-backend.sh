#!/bin/sh
set -e

echo "Waiting for PostgreSQL..."
until python -c "
import asyncio, os, sys
import asyncpg

async def check():
    url = os.environ.get('DATABASE_URL', '').replace('postgresql+asyncpg://', 'postgresql://')
    for _ in range(30):
        try:
            conn = await asyncpg.connect(url)
            await conn.close()
            return
        except Exception:
            await asyncio.sleep(2)
    sys.exit(1)

asyncio.run(check())
"; do
  sleep 2
done

echo "Running migrations..."
alembic upgrade head

echo "Ensuring admin user..."
python -m scripts.create_admin admin@example.com password || true

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
