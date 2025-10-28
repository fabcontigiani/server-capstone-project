import logging
import os
from django.shortcuts import render
from django.http import HttpResponse

from monitor.forms import MyImageForm
from monitor.models import MyImage

from monitor.service import process_image

from django.views.decorators.http import require_http_methods

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
        image = MyImage.objects.create(
            mac_address=mac_address,
            image=request.FILES["image"],
        )

        return HttpResponse("Image uploaded successfully.")
    except Exception as e:
        return HttpResponse("Error uploading image.")
