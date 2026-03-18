from django.shortcuts import render
from django.http import HttpResponse

from monitor.forms import MyImageForm
from monitor.models import MyImage

from monitor.service import process_image

# Create your views here.
def home(request):
    # Show only 4 most recent images
    last_items = MyImage.objects.order_by('-created_at')[:4]
    
    image_entries = []
    for img in last_items:
        md = img.metadata or {}
        db_top_class = (img.top_classification or '').strip()
        
        # 1. Extraer Detecciones (igual que en bot.py)
        predictions = md.get('predictions', {})
        raw_detections = predictions.get('detections', [])
        detections = []
        for det in raw_detections[:5]:  # Mostrar máx 5
            detections.append({
                'label': det.get('label', 'unknown'),
                'conf': f"{det.get('conf', 0):.1%}" # Formato porcentaje
            })

        # 2. Extraer Clasificaciones (igual que en bot.py)
        top_classifications = md.get('top_classifications', [])
        classifications = []
        for cls in top_classifications[:5]:
            class_name = cls.get("class", "unknown")
            # Limpiar nombre (quitar taxonomía larga si existe)
            display_name = class_name.split(";")[-1] if ";" in class_name else class_name
            rank = cls.get('rank')
            classifications.append({
                'rank': rank,
                'name': display_name,
                'score': cls.get('score_percent', '0%'),
                'is_model_top': rank == 1,
            })

        # Top clasificación a mostrar: preferir columna dedicada y luego fallback
        if db_top_class:
            top_classification = db_top_class
        elif classifications:
            top_classification = classifications[0]['name']
        else:
            top_classification = 'N/A'

        image_entries.append({
            'image': img,
            'detections': detections,
            'classifications': classifications,
            'created_at': img.created_at,
            'top_classification': top_classification,
            'feedback_edited_by_user': img.feedback_edited_by_user,
        })

    return render(request, 'home.html', {
        'title': 'Sistema de vigilancia distribuido',
        'image_pairs': last_items,
        'image_entries': image_entries,
    })

def upload(request):
    if request.method == 'POST':
        form = MyImageForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            process_image(obj)
            return HttpResponse("Image uploaded successfully.")
    return HttpResponse("Upload an image.")