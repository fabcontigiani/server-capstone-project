import os
import logging
from asgiref.sync import async_to_sync
from django.utils import timezone
from telegram import Bot, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram_bot.models import TelegramUser
from telegram_bot.bot import format_classification_results

logger = logging.getLogger(__name__)


async def _broadcast_results(
    chat_ids, original_bytes, processed_bytes, text_report, created_at,
    filter_reason="",
):
    """Función asíncrona para enviar medios y texto a todos los usuarios."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.warning("No TELEGRAM_BOT_TOKEN found. Skipping notification.")
        return

    bot = Bot(token=token)

    for chat_id in chat_ids:
        try:
            # Re-crear objetos multimedia para cada envío
            media_group = []
            created_at_local = timezone.localtime(created_at)
            caption = (
                f"Nueva imagen capturada\n{created_at_local.strftime('%d-%m-%Y %H:%M')}"
            )

            # Imagen original
            media_group.append(InputMediaPhoto(media=original_bytes, caption=caption))

            # Imagen procesada (si existe) - sin caption, Telegram solo muestra el primero
            if processed_bytes:
                media_group.append(InputMediaPhoto(media=processed_bytes))

            # Enviar grupo de fotos
            if len(media_group) > 1:
                await bot.send_media_group(chat_id=chat_id, media=media_group)
            else:
                await bot.send_photo(
                    chat_id=chat_id, photo=original_bytes, caption=caption
                )

            # Agregar pregunta de validación
            full_report = text_report
            full_report += "\n\n*¿La clasificación es correcta?*"

            # Crear botones inline
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("SI", callback_data="classification_correct_yes"),
                    InlineKeyboardButton("NO", callback_data="classification_correct_no"),
                ]
            ])

            # Enviar reporte de texto con botones
            await bot.send_message(
                chat_id=chat_id, text=full_report, parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Failed to send notification to {chat_id}: {e}")


def send_telegram_notification(instance, filter_reason=""):
    """
    Lee los datos de la imagen y los transmite a todos los usuarios de Telegram registrados.
    """
    try:
        # 1. Obtener destinatarios (usuarios que han iniciado el bot)
        chat_ids = list(TelegramUser.objects.values_list("chat_id", flat=True))
        if not chat_ids:
            return

        logger.warning(
            f"Preparing to send notification to {len(chat_ids)} users: {chat_ids}"
        )

        # 2. Preparar datos (leer archivos en memoria para evitar problemas de I/O en async)
        img_path = instance.image.path
        if not os.path.exists(img_path):
            logger.warning(f"Image file not found: {img_path}")
            return

        with open(img_path, "rb") as f:
            original_bytes = f.read()

        processed_bytes = None
        if instance.processed_image and os.path.exists(instance.processed_image.path):
            with open(instance.processed_image.path, "rb") as f:
                processed_bytes = f.read()

        # 3. Formatear texto usando la utilidad existente
        metadata = instance.metadata or {}
        text_report = format_classification_results(metadata)

        # 4. Ejecutar envío asíncrono desde contexto síncrono
        async_to_sync(_broadcast_results)(
            chat_ids, original_bytes, processed_bytes, text_report,
            instance.created_at, filter_reason=filter_reason,
        )
        logger.info(f"Sent Telegram notification to {len(chat_ids)} users.")

    except Exception as e:
        logger.error(f"Error in send_telegram_notification: {e}")
