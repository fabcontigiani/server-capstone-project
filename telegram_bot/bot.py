from __future__ import annotations

import os
import logging
from typing import Optional

from telegram import Update, InputFile
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


async def last(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the most recently uploaded image to the requesting chat.

    Looks up the latest `MyImage` by `created_at`, ensures the file exists,
    and sends it as a photo. If no image is available, replies with a message.
    """
    # find latest MyImage (sync ORM via sync_to_async)
    latest = await sync_to_async(lambda: MyImage.objects.order_by('-created_at').first())()
    if not latest:
        await update.message.reply_text("No images have been uploaded yet.")
        return

    # ensure file exists and send
    img_path = latest.image.path
    if not os.path.exists(img_path):
        await update.message.reply_text("Latest image file is missing on the server.")
        return

    try:
        # open file per-send to avoid stream exhaustion
        with open(img_path, 'rb') as f:
            await update.message.reply_photo(photo=InputFile(f), caption=f"Last image uploaded at {latest.created_at}")
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
