import os
import logging
from pathlib import Path

import requests
from django.core.files import File
from monitor.models import MyImage

from monitor.filters import should_send_notification
from telegram_bot.sender import send_telegram_notification

logger = logging.getLogger(__name__)

# SpeciesNet server URL (internal docker network)
SPECIESNET_URL = os.environ.get("SPECIESNET_URL", "http://speciesnet:8000")


def run_inference(image_path: str) -> dict:
    """Send the image to the local SpeciesNet server for detection and classification."""
    # SpeciesNet server expects file paths accessible to the server
    # Since we mount /app/media in both containers, use the container path
    payload = {"instances": [{"filepath": image_path}]}

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


def format_classifications(prediction: dict, top_n: int = 5) -> list[dict]:
    """Extract top N classification results from prediction."""
    classifications = prediction.get("classifications", {})
    classes = classifications.get("classes", [])
    scores = classifications.get("scores", [])

    results = []
    for i, (class_name, score) in enumerate(zip(classes[:top_n], scores[:top_n])):
        results.append(
            {
                "rank": i + 1,
                "class": class_name,
                "score": score,
                "score_percent": f"{score:.1%}",
            }
        )
    return results


def process_image(instance: MyImage) -> None:
    """Process an image through SpeciesNet for detection and classification.

    The external SpeciesNet service draws bounding boxes and saves the annotated
    image alongside the original. This function reads that annotated image path
    from the prediction response.
    """
    prediction = run_inference(instance.image.path)

    if "error" in prediction:
        logger.error(
            f"Inference failed for {instance.image.path}: {prediction['error']}"
        )
        instance.metadata = {"error": prediction["error"]}
        instance.save(update_fields=["metadata"])
        return

    # Extract classification results
    top_classifications = format_classifications(prediction)

    # Get the annotated image path from the prediction response
    annotated_filepath = prediction.get("annotated_filepath")

    if annotated_filepath and os.path.exists(annotated_filepath):
        # Copy the annotated image to the processed_images directory
        with open(annotated_filepath, "rb") as f:
            filename = f"processed_{Path(instance.image.name).name}"
            instance.processed_image.save(filename, File(f), save=False)
        # Remove the duplicate from the original location
        os.remove(annotated_filepath)

    # Save full prediction metadata including classifications
    instance.metadata = {
        "predictions": prediction,
        "top_classifications": top_classifications,
        "detections_count": len(prediction.get("detections", [])),
    }
    instance.save(update_fields=["processed_image", "metadata"])

    logger.info(
        f"Processed image {instance.image.path}: {len(prediction.get('detections', []))} detections"
    )

    # Decidir si enviar notificación por Telegram según la lógica de filtrado
    should_send, filter_reason = should_send_notification(prediction)
    if should_send:
        send_telegram_notification(instance, filter_reason=filter_reason)
        logger.info("Image passed filter → notification sent")
    else:
        logger.info("Image filtered out (%s) → no notification sent", filter_reason)
