import os
from django.shortcuts import render
from django.http import HttpResponse

from monitor.forms import MyImageForm
from monitor.models import MyImage

# Create your views here.
def home(request):
    last_five_items = MyImage.objects.order_by('-created_at')[:4]
    img_paths = set([item.image.url for item in last_five_items if os.path.exists(item.image.path)])

    return render(request, 'home.html', {'title': 'Sistema de vigilancia distribuido', 'img_paths': img_paths})

def upload(request):
    if request.method == 'POST':
        form = MyImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse("Image uploaded successfully.")
    return HttpResponse("Upload an image.")