Docker with Astral 'uv' images
================================

This project ships a Dockerfile and docker-compose that use the Astral `uv` images
(`ghcr.io/astral-sh/uv:python3.13-trixie-slim`) to build and run the Django app.

Summary
-------
- `Dockerfile` uses a two-stage build: `builder` runs `uv sync` to create a virtualenv
  and install dependencies, then `runtime` copies the environment and project.
- `docker-compose.yml` defines `web`, `bot` and `db` services. The `bot` runs the
  management command `run_telegram_bot` and shares the media volume so it can send
  uploaded images.

Quick start (development)
-------------------------
1. Copy `.env.sample` to `.env` and fill values (especially `TELEGRAM_BOT_TOKEN`).
2. Build and start services:

```bash
docker compose up --build
```

3. Visit http://localhost:8000. The Telegram bot can be started by running the `bot`
   service; it will register users when they send `/start` and `last` command will
   return the latest uploaded image.

Notes & next steps
------------------
- The provided `CMD` runs `manage.py runserver` for convenience. For production,
  replace the `CMD` in `Dockerfile` with a proper ASGI server (e.g. `uvicorn` or
  `gunicorn` + `uvicorn.workers.UvicornWorker`) and tune settings (workers, timeouts).
- Consider using named images for `web` and `bot` (or multi-stage targets) to avoid
  rebuilding the whole image twice.
- You may want to add a separate service for background tasks (Celery/RQ) if you
  decide to send notifications on upload asynchronously.
