from __future__ import annotations

import os
import logging
from typing import Optional
from django.utils import timezone

from telegram import Update, InputFile, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from asgiref.sync import sync_to_async

from telegram_bot.models import TelegramUser
from monitor.models import MyImage

logger = logging.getLogger(__name__)


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to /start with a simple greeting."""
    user = update.effective_user
    name = user.first_name if user and user.first_name else "there"
    # save chat id in DB (use sync_to_async because handlers are async)
    chat_id = update.effective_chat.id
    first_name = user.first_name if user else None
    username = user.username if user else None
    await sync_to_async(TelegramUser.objects.get_or_create)(
        chat_id=chat_id,
        defaults={
            'first_name': first_name,
            'username': username,
        },
    )
    await update.message.reply_text(f"Hello, {name}! This is the Django bot.")
    await update.message.reply_text(f"Chat ID: {chat_id}; Username: {username}")


async def echo(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo non-command text messages back to the user."""
    if update.message and update.message.text:
        await update.message.reply_text(f"You said: {update.message.text}")


def format_classification_results(metadata: dict) -> str:
    """Format classification results for display in Telegram."""
    if not metadata:
        return "No hay datos de análisis disponibles."
    
    if "error" in metadata:
        return f"Error en el análisis: {metadata['error']}"
    
    lines = []
    
    # Detection summary
    detections_count = metadata.get("detections_count", 0)
    if detections_count > 0:
        lines.append(f"*Detecciones:* {detections_count} objeto(s) encontrados")
        
        # Show detection labels from predictions
        predictions = metadata.get("predictions", {})
        detections = predictions.get("detections", [])
        for det in detections[:5]:  # Show up to 5 detections
            label = det.get("label", "unknown")
            conf = det.get("conf", 0)
            lines.append(f"  • {label}: {conf:.1%}")
    else:
        lines.append("*Detecciones:* No se detectaron objetos")
    
    lines.append("")
    
    # Classification results
    top_classifications = metadata.get("top_classifications", [])
    if top_classifications:
        lines.append("*Clasificaciones principales:*")
        for cls in top_classifications[:5]:
            rank = cls.get("rank", "?")
            class_name = cls.get("class", "unknown")
            score_percent = cls.get("score_percent", "0%")
            # Clean up the class name (species taxonomy format)
            display_name = class_name.split(";")[-1] if ";" in class_name else class_name
            lines.append(f"  {rank}. {display_name} ({score_percent})")
    else:
        lines.append("*Clasificaciones:* No hay datos de clasificación")
    
    return "\n".join(lines)


async def last(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the most recently uploaded image with analysis results.

    Sends the original photo, the processed photo with detections,
    and a list of top classification results.
    """
    # find latest MyImage (sync ORM via sync_to_async)
    latest = await sync_to_async(lambda: MyImage.objects.order_by('-created_at').first())()
    if not latest:
        await update.message.reply_text("No images have been uploaded yet.")
        return

    # Paths
    img_path = latest.image.path
    processed_path = latest.processed_image.path if latest.processed_image else None
    
    if not os.path.exists(img_path):
        await update.message.reply_text("Latest image file is missing on the server.")
        return

    try:
        created_at_local = timezone.localtime(latest.created_at)

        # Prepare media group with original and processed images
        media_group = []
        
        # Original image
        with open(img_path, 'rb') as f:
            original_bytes = f.read()
        media_group.append(InputMediaPhoto(
            media=original_bytes,
            caption=f"Imagen original cargada el {created_at_local.strftime('%d-%m-%Y %H:%M')}"
        ))
        
        # Processed image with detections (if available)
        if processed_path and os.path.exists(processed_path):
            with open(processed_path, 'rb') as f:
                processed_bytes = f.read()
            media_group.append(InputMediaPhoto(
                media=processed_bytes,
                caption="Imagen procesada con detecciones"
            ))
        
        # Send media group
        if len(media_group) > 1:
            await update.message.reply_media_group(media=media_group)
        else:
            # Just send original if no processed image
            await update.message.reply_photo(
                photo=original_bytes,
                caption=f"Imagen cargada el {created_at_local.strftime('%d-%m-%Y %H:%M')}"
            )
        
        # Send classification results as text
        metadata = latest.metadata or {}
        results_text = format_classification_results(metadata)
        await update.message.reply_text(results_text, parse_mode='Markdown')
        
    except Exception as exc:  # pragma: no cover - best-effort send
        logger.exception("Failed to send last image: %s", exc)
        await update.message.reply_text("Failed to send the image.")


def create_application(token: Optional[str] = None):
    """Build and return a telegram Application instance.

    Token is read from TELEGRAM_BOT_TOKEN environment variable if not passed.
    """
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Telegram token is required: set TELEGRAM_BOT_TOKEN or pass token")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("last", last))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    return app


def run(token: Optional[str] = None) -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting telegram bot (polling)")
    app = create_application(token=token)
    app.run_polling()

