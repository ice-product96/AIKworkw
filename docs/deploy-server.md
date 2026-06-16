# Деплой на удалённый Linux-сервер

Для сервера, где **уже заняты порты 80, 443, 9000** (хостовый nginx и другие сервисы).

## Требования

- Docker + Docker Compose
- Git
- Хостовый nginx с SSL (Let's Encrypt)

## Быстрый старт

```bash
git clone https://github.com/ice-product96/AIKworkw.git
cd AIKworkw

cp .env.prod.example .env.prod
nano .env.prod   # пароли, JWT_SECRET, CORS_ORIGINS (ваш домен)

chmod +x scripts/deploy-prod.sh
./scripts/deploy-prod.sh
```

## Что поднимается

| Сервис    | Доступ с хоста                         |
|-----------|----------------------------------------|
| postgres  | только внутри Docker-сети              |
| redis     | только внутри Docker-сети              |
| minio     | только внутри Docker-сети              |
| backend   | только через frontend (`/api/`)      |
| frontend  | `127.0.0.1:8011` → прокси host nginx   |

Порты **5432, 6379, 8000, 9000** на хост **не занимаются** — конфликтов с существующими сервисами нет.

## Nginx на хосте

```bash
sudo cp docker/nginx-host.example.conf /etc/nginx/sites-available/aikworkw
sudo nano /etc/nginx/sites-available/aikworkw   # замените домен и пути к SSL
sudo ln -sf /etc/nginx/sites-available/aikworkw /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Обновление

```bash
cd ~/AIKworkw
git pull
./scripts/deploy-prod.sh
```

## Админ

При первом старте: `admin@example.com` / `password` — **смените пароль**.

## Логи и остановка

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f
docker compose -f docker-compose.prod.yml --env-file .env.prod down
```

## Локальная разработка (Windows)

```powershell
docker compose up --build
```

Или `.\scripts\docker-up.ps1` — полный стек с nginx на `http://localhost`.
