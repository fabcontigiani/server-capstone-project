"""
Filtrado inteligente de imágenes antes de envío por Telegram.

Usa una combinación de la confianza de detección y las clasificaciones
de especies para decidir si una imagen es relevante o un falso positivo/vacía.
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Umbrales (ajustar según sea necesario)
# ---------------------------------------------------------------------------
DETECTION_HIGH = 0.80      # Aceptación directa
DETECTION_MID = 0.50       # Conflicto interesante (animal lejos / pequeño)
DETECTION_LOW = 0.30       # Por debajo → detección débil
CLASSIFICATION_MIN = 0.30  # Confianza mínima para "Clasificación Segura"


def _normalize_class(raw_name: str) -> str:
    """Extract the display name from SpeciesNet taxonomy-format class names.

    SpeciesNet returns names like 'taxonomy;subtax;blank' — we only care
    about the last segment, which is the same logic used in bot.py and views.py.
    """
    return raw_name.split(";")[-1].strip().lower()


def get_max_detection_confidence(prediction: dict) -> float:
    """Return the highest detection confidence across all labels.

    Considers all object types (animal, human, vehicle) as relevant.
    """
    detections = prediction.get("detections", [])
    if not detections:
        return 0.0
    return max(det.get("conf", 0.0) for det in detections)


def get_non_blank_score(prediction: dict) -> float:
    """Sum classification probabilities for all classes that are NOT 'blank'.

    This is a proxy for "how likely is it that there is *something* in the image".
    """
    classifications = prediction.get("classifications", {})
    classes = classifications.get("classes", [])
    scores = classifications.get("scores", [])

    return sum(
        score
        for cls, score in zip(classes, scores)
        if _normalize_class(cls) != "blank"
    )


def get_top_class(prediction: dict) -> tuple[str, float]:
    """Return (normalized_class_name, score) for the #1 classification.

    Returns ("", 0.0) if no classifications are available.
    Class names are normalized to strip SpeciesNet taxonomy prefixes.
    """
    classifications = prediction.get("classifications", {})
    classes = classifications.get("classes", [])
    scores = classifications.get("scores", [])

    if classes and scores:
        return _normalize_class(classes[0]), scores[0]
    return "", 0.0


def should_send_notification(prediction: dict) -> tuple[bool, str]:
    """Decide whether an image is worth sending via Telegram.

    Returns (should_send, reason) where reason describes the decision.

    Decision matrix
    ───────────────────────────────────────────────────────────────────────────
    Escenario             | Detección         | Clasificación         | Enviar
    ───────────────────────────────────────────────────────────────────────────
    Aceptación Directa    | max > 80%         | cualquiera            | Sí
    Conflicto Interesante | max > 50%         | top = blank           | Sí
    Clasificación Segura  | cualquiera        | top ≠ blank (> 30%)   | Sí
    Detección Débil       | max < 30%         | top = blank           | No
    Default               | resto             |                       | Sí
    ───────────────────────────────────────────────────────────────────────────
    """
    max_det = get_max_detection_confidence(prediction)
    top_class, top_score = get_top_class(prediction)
    non_blank = get_non_blank_score(prediction)
    top_is_blank = top_class.lower() == "blank"

    logger.info(
        "Filter check — max_det=%.1f%%, top_class=%s (%.1f%%), non_blank=%.1f%%",
        max_det * 100,
        top_class,
        top_score * 100,
        non_blank * 100,
    )

    # 1. Aceptación Directa: alta certeza de presencia
    if max_det > DETECTION_HIGH:
        reason = f"✅ Aceptación Directa (detección {max_det:.0%})"
        logger.info("Filter → SEND (%s)", reason)
        return True, reason

    # 2. Clasificación Segura: el clasificador está seguro de que hay algo
    if not top_is_blank and top_score > CLASSIFICATION_MIN:
        reason = f"✅ Clasificación Segura ({top_class} {top_score:.1%})"
        logger.info("Filter → SEND (%s)", reason)
        return True, reason

    # 3. Conflicto Interesante: hay detección razonable pero clasificador dice blank
    if max_det > DETECTION_MID and top_is_blank:
        reason = f"⚠️ Conflicto Interesante (detección {max_det:.0%} pero clasificación=blank)"
        logger.info("Filter → SEND (%s)", reason)
        return True, reason

    # 4. Detección Débil + blank → probable falso positivo / viento
    if max_det < DETECTION_LOW and top_is_blank:
        reason = f"Detección Débil ({max_det:.0%} + blank)"
        logger.info("Filter → IGNORE (%s)", reason)
        return False, reason

    # 5. Default: enviar por precaución
    reason = "ℹ️ Default (enviado por precaución)"
    logger.info("Filter → SEND (%s)", reason)
    return True, reason
