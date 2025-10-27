import requests
from monitor.models import MyImage
import os, io
from PIL import Image, ImageDraw, ImageFont

from telegram_bot.bot import send_processed_image

def run_inference(image_path: str) -> dict[str, any]:
    """Envia la imagen a la API de detección de animales."""
    files = {"image": ("image.jpg", open(image_path, "rb"), "image/jpeg")}
    data = {"country": "ARG", "threshold": 0.2}
    headers = {"Authorization": os.environ.get("ANIMAL_DETECT_API_KEY", "")}
    response = requests.post(
        "https://www.animaldetect.com/api/v1/detect",
        files=files,
        data=data,
        headers=headers,
    )
    result = response.json()
    return result

def render_detections(image_path: str, detections: dict[str, any]) -> bytes:
    """Dibuja detecciones con bbox normalizado [x, y, w, h] convertido a píxeles."""
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    W, H = img.size

    font = ImageFont.load_default()

    for ann in detections.get("annotations", []):
        x = int(ann['bbox'][0] * W)
        y = int(ann['bbox'][1] * H)
        w = int(ann['bbox'][2] * W)
        h = int(ann['bbox'][3] * H)

        # Rectángulo
        draw.rectangle([x, y, x + w, y + h], outline='red', width=3)

        # Etiqueta con fondo
        label = f"{ann.get('label','')} ({ann.get('score',0.0):.2%})"
        text_bbox = draw.textbbox((x, max(0, y - 24)), label, font=font)
        draw.rectangle(text_bbox, fill='red')
        draw.text((text_bbox[0], text_bbox[1]), label, fill='white', font=font)

    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()

def process_image(instance: MyImage) -> None:
    inference = run_inference(instance.image.path)
    rendered = render_detections(instance.image.path, inference)

    filename = f"processed_{os.path.basename(instance.image.name)}"
    instance.processed_image.save(filename, content=io.BytesIO(rendered), save=False)
    instance.metadata = inference
    instance.save(update_fields=['processed_image', 'metadata'])

    # send_processed_image()

    # print("Inference result:", inference)
