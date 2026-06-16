#!/bin/sh
set -e

echo "Waiting for Redis..."
until python -c "
import os, redis, sys
url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
for _ in range(30):
    try:
        redis.from_url(url).ping()
        break
    except Exception:
        import time; time.sleep(2)
else:
    sys.exit(1)
"; do
  sleep 2
done

exec celery -A app.workers.tasks worker -l info --concurrency=2
