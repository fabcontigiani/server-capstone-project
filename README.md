# Wildlife Detection Capstone Project

A Django-based wildlife monitoring system that uses Google's SpeciesNet ML model to detect and classify animals in images. The system includes a web interface for image uploads, automated ML processing, and a Telegram bot for notifications and results delivery.

## Features

- 📸 **Image Upload & Management**: Web interface for uploading and viewing wildlife images
- 🤖 **AI-Powered Detection**: Automatic animal detection using SpeciesNet (YOLOv5-based detector)
- 🏷️ **Species Classification**: Multi-label classification identifying species with confidence scores
- 📱 **Telegram Bot Integration**: Receive notifications and query results via Telegram
- 🎨 **Visual Results**: Annotated images with bounding boxes and confidence scores
- 🐳 **Docker Deployment**: Fully containerized with docker-compose

## Architecture

The project consists of four main services:

1. **Web Service** (Django): Main application server with admin interface and image management
2. **Bot Service** (Python Telegram Bot): Telegram bot for user interactions
3. **SpeciesNet Service**: Pre-built ML inference container from `ghcr.io/fabcontigiani/wildlife-detection-capstone-project`
4. **Database** (PostgreSQL): Data persistence

The ML inference service handles both detection/classification and image annotation, returning annotated images alongside the original files.

## Prerequisites

- Docker & Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Optional: NVIDIA GPU + nvidia-container-toolkit for faster inference

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd server-capstone-project
   ```

2. **Configure environment variables**
   ```bash
   cp .env.sample .env
   # Edit .env and add your TELEGRAM_BOT_TOKEN and other settings
   ```

3. **Start all services**
   ```bash
   docker compose up --build
   ```

4. **Access the application**
   - Web interface: http://localhost:8000
   - SpeciesNet API: http://localhost:8002
   - Telegram bot: Search for your bot on Telegram and send `/start`

**Note**: First startup takes 5-10 minutes as SpeciesNet downloads the model files (~2GB). Subsequent starts are much faster.

## Usage

### Web Interface

1. Navigate to http://localhost:8000
2. Upload an image through the interface
3. The system automatically processes it through SpeciesNet
4. View the original and annotated images with detection results

### Telegram Bot

Commands:
- `/start` - Register and get welcome message
- `/last` - Retrieve the most recent processed image with:
  - Original photo
  - Processed photo with detection bounding boxes
  - List of detections with confidence scores
  - Top 5 species classifications

### Direct API Access

Make predictions directly to the SpeciesNet server:

```bash
curl -X POST http://localhost:8002/predict \
  -H "Content-Type: application/json" \
  -d '{"instances": [{"filepath": "/app/media/images/your_image.jpg"}]}'
```

Response includes:
- `detections`: Bounding boxes with labels (animal/human/vehicle) and confidence
- `classifications`: Species predictions with confidence scores
- `annotated_filepath`: Path to the annotated image with bounding boxes

## Development

### Local Python Environment

For local development without Docker:

```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Activate environment
source .venv/bin/activate

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Project Structure

```
├── capstoneproject/      # Django project settings
├── monitor/              # Main app for image management
│   ├── models.py        # MyImage model
│   ├── service.py       # SpeciesNet integration
│   └── views.py         # Web views
├── telegram_bot/         # Telegram bot app
│   ├── bot.py           # Bot handlers and logic
│   └── models.py        # TelegramUser model
├── media/               # Uploaded images (Docker volume)
├── static/              # Static files
├── Dockerfile           # Web/bot service image
└── docker-compose.yml   # Service orchestration
```

## Configuration

### Environment Variables

Key variables in `.env`:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (required)
- `SPECIESNET_URL`: SpeciesNet server URL (default: `http://speciesnet:8000`)
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Database credentials
- `GUNICORN_WORKERS`: Number of Gunicorn workers for web service
- `DJANGO_SECRET_KEY`: Django secret key for production

### GPU Acceleration

For faster inference with NVIDIA GPU:

1. Install [nvidia-container-toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Uncomment the `deploy` section in `docker-compose.yml` under `speciesnet` service
3. Restart services

## Technology Stack

- **Backend**: Django 5.2, Python 3.13
- **ML Service**: Pre-built container from `ghcr.io/fabcontigiani/wildlife-detection-capstone-project`
- **Bot Framework**: python-telegram-bot
- **Database**: PostgreSQL 15
- **Deployment**: Docker, Docker Compose, Gunicorn with Uvicorn workers
- **Package Manager**: uv (Astral)

## Model Information

**SpeciesNet** by Google:
- Detection: YOLOv5-based object detector for animals, humans, and vehicles
- Classification: Multi-label species classifier trained on wildlife imagery
- Model size: ~2GB
- Inference time: ~1-5 seconds per image (CPU), ~0.5-1 second (GPU)

## Troubleshooting

### SpeciesNet not responding
- Check if the container is still starting: `docker compose logs speciesnet`
- Model download can take time on first run
- Ensure enough disk space for model cache (~3GB)

### Telegram bot not responding
- Verify `TELEGRAM_BOT_TOKEN` is set correctly in `.env`
- Check bot service logs: `docker compose logs bot`
- Ensure bot service is running: `docker compose ps`

### Images not processing
- Check that all services are running: `docker compose ps`
- Verify media volume is mounted: `docker compose config`
- Check service logs for errors: `docker compose logs web`

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project uses SpeciesNet, which is licensed under the Apache License 2.0.

## Acknowledgments

- [SpeciesNet by Google](https://github.com/google/speciesnet) - ML model for wildlife detection and classification
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram bot framework
- [Astral uv](https://github.com/astral-sh/uv) - Fast Python package manager
