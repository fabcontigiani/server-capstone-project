from django.shortcuts import render
from django.http import HttpResponse

from monitor.forms import MyImageForm
from monitor.models import MyImage

# Create your views here.
def home(request):
    latest_image = MyImage.objects.last()
    if latest_image:
        img_path = latest_image.image.url

    return render(request, 'home.html', {'title': 'Sistema de vigilancia distribuido', 'img_path': img_path})

def upload(request):
    if request.method == 'POST':
        form = MyImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse("Image uploaded successfully.")
    return HttpResponse("Upload an image.")