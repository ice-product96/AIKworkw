FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends bash && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY docker/entrypoint-worker.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV PYTHONPATH=/app
ENTRYPOINT ["/entrypoint.sh"]
