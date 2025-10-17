# syntax=docker/dockerfile:1.4
################################################################################
# Builder stage using Astral 'uv' image to install dependencies into a virtualenv
################################################################################
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS builder

WORKDIR /app

# Copy only lock and pyproject first to leverage layer caching for deps
COPY pyproject.toml uv.lock* ./

# Use buildkit cache for uv's downloads and install only dependencies first
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-editable

# Copy the project and install it into the environment
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

################################################################################
# Final image
################################################################################
FROM ghcr.io/astral-sh/uv:python3.13-trixie-slim AS runtime

WORKDIR /app

# Copy the synced virtualenv and the project from the builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=capstoneproject.settings
ENV UV_COMPILE_BYTECODE=1

EXPOSE 8000

# Copy an entrypoint that runs migrations and collectstatic before starting the main process
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

# Default command (development): start Django dev server. Replace with uvicorn/gunicorn in production.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
