import requests
from monitor.models import MyImage
import os, io
from PIL import Image
from speciesnet import draw_bboxes
import logging

logger = logging.getLogger(__name__)

# SpeciesNet server URL (internal docker network)
SPECIESNET_URL = os.environ.get("SPECIESNET_URL", "http://speciesnet:8000")


def run_inference(image_path: str) -> dict[str, any]:
    """Send the image to the local SpeciesNet server for detection and classification."""
    # SpeciesNet server expects file paths accessible to the server
    # Since we mount /app/media in both containers, use the container path
    payload = {
        "instances": [
            {"filepath": image_path}
        ]
    }
    
    try:
        response = requests.post(
            f"{SPECIESNET_URL}/predict",
            json=payload,
            timeout=120,  # Model inference can be slow
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract the first prediction from the response
        predictions = result.get("predictions", [])
        if predictions:
            return predictions[0]
        return {"error": "No predictions returned"}
        
    except requests.exceptions.RequestException as e:
        logger.error(f"SpeciesNet API error: {e}")
        return {"error": str(e)}


def render_detections(image_path: str, prediction: dict[str, any]) -> bytes:
    """Draw detection bounding boxes on the image using SpeciesNet's draw_bboxes."""
    img = Image.open(image_path).convert("RGB")
    
    detections = prediction.get("detections", [])
    if detections:
        # Use speciesnet's draw_bboxes function
        img = draw_bboxes(img, detections)
        # Convert RGBA back to RGB for JPEG saving
        img = img.convert("RGB")
    
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=90)
    return buf.getvalue()


def format_classifications(prediction: dict[str, any], top_n: int = 5) -> list[dict]:
    """Extract top N classification results from prediction."""
    classifications = prediction.get("classifications", {})
    classes = classifications.get("classes", [])
    scores = classifications.get("scores", [])
    
    results = []
    for i, (class_name, score) in enumerate(zip(classes[:top_n], scores[:top_n])):
        results.append({
            "rank": i + 1,
            "class": class_name,
            "score": score,
            "score_percent": f"{score:.1%}"
        })
    return results


def process_image(instance: MyImage) -> None:
    """Process an image through SpeciesNet for detection and classification."""
    prediction = run_inference(instance.image.path)
    
    if "error" in prediction:
        logger.error(f"Inference failed for {instance.image.path}: {prediction['error']}")
        instance.metadata = {"error": prediction["error"]}
        instance.save(update_fields=['metadata'])
        return
    
    # Render detections on image
    rendered = render_detections(instance.image.path, prediction)
    
    # Extract classification results
    top_classifications = format_classifications(prediction)
    
    # Save processed image
    filename = f"processed_{os.path.basename(instance.image.name)}"
    instance.processed_image.save(filename, content=io.BytesIO(rendered), save=False)
    
    # Save full prediction metadata including classifications
    instance.metadata = {
        "predictions": prediction,
        "top_classifications": top_classifications,
        "detections_count": len(prediction.get("detections", [])),
    }
    instance.save(update_fields=['processed_image', 'metadata'])
    
    logger.info(f"Processed image {instance.image.path}: {len(prediction.get('detections', []))} detections")

