Docker with Astral 'uv' images
================================

This project ships a Dockerfile and docker-compose that use the Astral `uv` images
(`ghcr.io/astral-sh/uv:python3.13-trixie-slim`) to build and run the Django app.

Summary
-------
- `Dockerfile` uses a two-stage build: `builder` runs `uv sync` to create a virtualenv
  and install dependencies, then `runtime` copies the environment and project.
- `speciesnet.Dockerfile` builds a dedicated container for the SpeciesNet ML server
  which provides animal detection and classification via HTTP API.
- `docker-compose.yml` defines `web`, `bot`, `speciesnet` and `db` services. The `bot` runs the
  management command `run_telegram_bot` and shares the media volume so it can send
  uploaded images.

Quick start (development)
-------------------------
1. Copy `.env.sample` to `.env` and fill values (especially `TELEGRAM_BOT_TOKEN`).
2. Build and start services:

```bash
docker compose up --build
```

3. Visit http://localhost:8000 for the web app. The SpeciesNet API is available at
   http://localhost:8002/predict for direct testing.

4. The Telegram bot can be started by running the `bot` service; it will register users
   when they send `/start` and the `/last` command will return the latest uploaded image
   along with the processed image showing detections and classification results.

Services
--------
- **web**: Django application server (port 8000)
- **bot**: Telegram bot for notifications and image retrieval
- **speciesnet**: ML server for animal detection/classification (port 8002)
- **db**: PostgreSQL database

SpeciesNet Server
-----------------
The SpeciesNet service runs Google's SpeciesNet model for wildlife detection and
classification. On first startup, it will download the model files (~2GB) which
are cached in a Docker volume for persistence.

To make predictions directly to the SpeciesNet server:

```bash
curl -X POST http://localhost:8002/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [{"filepath": "/app/media/images/your_image.jpg"}]}'
```

GPU Support
-----------
To enable GPU acceleration for SpeciesNet (recommended for production), uncomment
the `deploy` section in docker-compose.yml for the `speciesnet` service. You'll need
the NVIDIA Container Toolkit installed.

How It Works
------------
When an image is uploaded through the web interface:

1. Django saves the image and triggers processing
2. `service.py` sends the image path to the SpeciesNet server (`http://speciesnet:8000/predict`)
3. SpeciesNet performs detection (bounding boxes) and classification (species identification)
4. Results are saved to the database as JSON metadata
5. Processed image with bounding boxes is generated using `speciesnet.draw_bboxes()`
6. Telegram bot can retrieve and display both images plus classification results

Notes & Best Practices
----------------------
- The image runs `gunicorn` with `uvicorn` workers by default. Tune worker count with
  the `GUNICORN_WORKERS` environment variable in `docker-compose.yml` or `.env`
- SpeciesNet model files (~2GB) are cached in a Docker volume for faster restarts
- First startup takes 5-10 minutes for model download; subsequent starts are ~30 seconds
- For production, enable GPU support for 3-5x faster inference
- Monitor SpeciesNet container logs during first startup to track model download progress
- The `/app/media` directory is shared between web, bot, and speciesnet containers

