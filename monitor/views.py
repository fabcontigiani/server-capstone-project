from django.shortcuts import render
from django.http import HttpResponse

from monitor.models import MyImage
from monitor.models import MacTelegramRelation

from monitor.service import process_image

from django.views.decorators.http import require_http_methods

from telegram_bot.bot import send_processed_image

from asgiref.sync import async_to_sync

# Create your views here.
def home(request):
    # Show only 4 most recent images not processed
    last_items = MyImage.objects.order_by('-created_at')[:4]

    return render(request, 'home.html', {'title': 'Sistema de vigilancia distribuido', 'image_pairs': last_items})

@require_http_methods(["POST"])
def upload(request):

    # Check if image exists in POST
    if "image" not in request.FILES:
        return HttpResponse("No image uploaded.")

    mac_address = request.POST.get("mac_address", "").strip().upper()

    if not mac_address or len(mac_address) != 17:
        return HttpResponse("Invalid MAC address.")
    
    try:
        # Save MyImage instance
        image = MyImage.objects.create(
            mac_address=mac_address,
            image=request.FILES["image"],
        )

        # Process image (blocking/synchronous)
        process_image(image)

        # Get metadata after processing to send trough Telegram bot
        metadata = image.metadata

        # Get datetime of image creation
        created_at = image.created_at

        # Find ID of Telegram chat to notify
        try:
            relation = MacTelegramRelation.objects.get(mac_address=mac_address)
            telegram_chat_id = relation.telegram_chat_id
            async_to_sync(send_processed_image)(telegram_chat_id, image.image.path, image.processed_image.path, metadata, created_at)
        except MacTelegramRelation.DoesNotExist:
            return HttpResponse("No Telegram chat registered for this MAC address.")

        return HttpResponse("Image uploaded and processed successfully.")
    except Exception as e:
        return HttpResponse("Error uploading or processing image.")
