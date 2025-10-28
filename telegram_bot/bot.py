from __future__ import annotations

from datetime import datetime
import os
import logging
from typing import Optional

from telegram import Update, InputFile, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
from asgiref.sync import sync_to_async

from telegram_bot.models import TelegramUser
from monitor.models import MyImage
from monitor.models import MacTelegramRelation

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


# Send images to especific chat ID
async def send_processed_image(telegram_chat_id: int, original_image_path: str, processed_image_path: str, metadata: dict[str, any], created_at: datetime) -> None:
    """Send original and processed images to the specified Telegram chat ID."""
    
    bot = Bot(token=os.environ.get("TELEGRAM_BOT_TOKEN"))
    
    try:
        with open(original_image_path, 'rb') as orig_file:
            await bot.send_photo(chat_id=telegram_chat_id, photo=InputFile(orig_file), caption="Original Image")

        with open(processed_image_path, 'rb') as proc_file:
            await bot.send_photo(chat_id=telegram_chat_id, photo=InputFile(proc_file), caption="Processed Image")

        # Send metadata as a message
        metadata_message = "Detections:\n"
        for ann in metadata.get("annotations", []):
            label = ann.get('label', 'unknown')
            score = ann.get('score', 0.0)
            metadata_message += f"- {label}: {score:.2%}\n"
        await bot.send_message(chat_id=telegram_chat_id, text=metadata_message)

        # Send creation time format to dd-mm-YYYY HH:MM:SS
        created_at_str = created_at.strftime("%d-%m-%Y %H:%M:%S")
        await bot.send_message(chat_id=telegram_chat_id, text=f"Image created at: {created_at_str}")

    except Exception as e:
        logger.error("Failed to send images: %s", e)

async def register_mac(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Register MAC address to the user chat ID."""

    if not update.message or not update.message.text:
        await update.message.reply_text("Please provide a MAC address.")
        return

    # mac_address = update.message.text.strip().upper()
    mac_address = update.message.text.split(" ")[-1].strip().upper()

    logging.info("Registering MAC address %s for chat ID %s, length %d", mac_address, update.effective_chat.id, len(mac_address))

    if len(mac_address) != 17:
        await update.message.reply_text("Invalid MAC address format. Please provide a valid MAC address.")
        return
    
    chat_id = update.effective_chat.id

    # Create or update the MacTelegramRelation
    _, created = await sync_to_async(MacTelegramRelation.objects.update_or_create)(
        mac_address=mac_address,
        defaults={'telegram_chat_id': chat_id},
    )
    if created:
        await update.message.reply_text(f"MAC address {mac_address} registered successfully.")
    else:
        await update.message.reply_text(f"MAC address {mac_address} updated successfully.")

def create_application(token: Optional[str] = None):
    """Build and return a telegram Application instance.

    Token is read from TELEGRAM_BOT_TOKEN environment variable if not passed.
    """
    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Telegram token is required: set TELEGRAM_BOT_TOKEN or pass token")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("register_mac", register_mac))

    app.add_handler(CommandHandler("last", last))
    # app.add_handler(CommandHandler("last_processed", send_processed_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    return app


def run(token: Optional[str] = None) -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting telegram bot (polling)")
    app = create_application(token=token)
    app.run_polling()
