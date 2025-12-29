from django.shortcuts import render
from django.http import HttpResponse

from monitor.forms import MyImageForm
from monitor.models import MyImage

from monitor.service import process_image


# Create your views here.
def home(request):
    # Show only 4 most recent images
    last_items = MyImage.objects.order_by("-created_at")[:4]

    image_entries = []
    for img in last_items:
        md = img.metadata or {}

        # 1. Extract Detections (same as in bot.py)
        predictions = md.get("predictions", {})
        raw_detections = predictions.get("detections", [])
        detections = []
        for det in raw_detections[:5]:  # Show max 5
            detections.append(
                {
                    "label": det.get("label", "unknown"),
                    "conf": f"{det.get('conf', 0):.1%}",  # Percentage format
                }
            )

        # 2. Extract Classifications (same as in bot.py)
        top_classifications = md.get("top_classifications", [])
        classifications = []
        for cls in top_classifications[:5]:
            class_name = cls.get("class", "unknown")
            # Clean name (remove long taxonomy if present)
            display_name = (
                class_name.split(";")[-1] if ";" in class_name else class_name
            )
            classifications.append(
                {
                    "rank": cls.get("rank"),
                    "name": display_name,
                    "score": cls.get("score_percent", "0%"),
                }
            )

        image_entries.append(
            {
                "image": img,
                "detections": detections,
                "classifications": classifications,
                "created_at": img.created_at,
            }
        )

    return render(
        request,
        "home.html",
        {
            "title": "Distributed Surveillance System",
            "image_pairs": last_items,
            "image_entries": image_entries,
        },
    )


def upload(request):
    if request.method == "POST":
        form = MyImageForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save()
            process_image(obj)
            return HttpResponse("Image uploaded successfully.")
    return HttpResponse("Upload an image.")
