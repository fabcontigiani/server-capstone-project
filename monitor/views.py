import os
from django.shortcuts import render
from django.http import HttpResponse

from monitor.forms import MyImageForm
from monitor.models import MyImage

from monitor.service import process_image

# Create your views here.
def home(request):
    # Get last images with their processed versions
    last_items = MyImage.objects.order_by('-created_at')[:4]
    # Filter only items where the original image exists
    image_pairs = [item for item in last_items if os.path.exists(item.image.path)]

    return render(request, 'home.html', {'title': 'Sistema de vigilancia distribuido', 'image_pairs': image_pairs})

def upload(request):
    if request.method == 'POST':
        form = MyImageForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            process_image(obj)
            return HttpResponse("Image uploaded successfully.")
    return HttpResponse("Upload an image.")