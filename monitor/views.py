from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return HttpResponse("Hello, this is the home page of the monitor app.")

def upload(request):
    if request.method == 'POST' and request.FILES.get('file'):
        image = request.FILES['file']
        # Process the uploaded image
        return HttpResponse("Image uploaded successfully.")
    return HttpResponse("Upload an image.")