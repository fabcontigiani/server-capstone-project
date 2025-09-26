from django.shortcuts import render
from django.http import HttpResponse

from monitor.forms import MyImageForm

# Create your views here.
def home(request):
    return HttpResponse("Hello, this is the home page of the monitor app.")

def upload(request):
    if request.method == 'POST':
        form = MyImageForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponse("Image uploaded successfully.")
    return HttpResponse("Upload an image.")