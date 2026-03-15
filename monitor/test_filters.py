"""
Tests for the image filtering decision matrix in monitor/filters.py.
"""

from django.test import TestCase

from monitor.filters import (
    _normalize_class,
    get_max_detection_confidence,
    get_non_blank_score,
    get_top_class,
    should_send_notification,
)


def _make_prediction(detections=None, classes=None, scores=None):
    """Helper to build a prediction dict mirroring SpeciesNet output."""
    pred = {}
    if detections is not None:
        pred["detections"] = detections
    if classes is not None or scores is not None:
        pred["classifications"] = {
            "classes": classes or [],
            "scores": scores or [],
        }
    return pred


# ── Normalize helper ─────────────────────────────────────────────────────────

class NormalizeClassTests(TestCase):
    def test_plain_name(self):
        self.assertEqual(_normalize_class("blank"), "blank")

    def test_taxonomy_format(self):
        self.assertEqual(_normalize_class("taxonomy;subtax;blank"), "blank")

    def test_single_semicolon(self):
        self.assertEqual(_normalize_class("genus;human"), "human")

    def test_strips_whitespace(self):
        self.assertEqual(_normalize_class(" blank "), "blank")


# ── Helper function tests ────────────────────────────────────────────────────

class GetMaxDetectionConfidenceTests(TestCase):
    def test_empty_detections(self):
        pred = _make_prediction(detections=[])
        self.assertEqual(get_max_detection_confidence(pred), 0.0)

    def test_no_detections_key(self):
        self.assertEqual(get_max_detection_confidence({}), 0.0)

    def test_single_animal(self):
        pred = _make_prediction(detections=[{"label": "animal", "conf": 0.648}])
        self.assertAlmostEqual(get_max_detection_confidence(pred), 0.648)

    def test_multiple_labels_picks_max(self):
        pred = _make_prediction(detections=[
            {"label": "human", "conf": 0.943},
            {"label": "human", "conf": 0.908},
            {"label": "vehicle", "conf": 0.875},
        ])
        self.assertAlmostEqual(get_max_detection_confidence(pred), 0.943)


class GetNonBlankScoreTests(TestCase):
    def test_all_blank(self):
        pred = _make_prediction(classes=["blank"], scores=[0.974])
        self.assertAlmostEqual(get_non_blank_score(pred), 0.0)

    def test_taxonomy_blank_excluded(self):
        pred = _make_prediction(classes=["taxonomy;blank"], scores=[0.974])
        self.assertAlmostEqual(get_non_blank_score(pred), 0.0)

    def test_mixed(self):
        pred = _make_prediction(
            classes=["blank", "bird", "red-breasted coua", "human"],
            scores=[0.974, 0.013, 0.001, 0.001],
        )
        self.assertAlmostEqual(get_non_blank_score(pred), 0.015, places=5)

    def test_no_classifications(self):
        self.assertAlmostEqual(get_non_blank_score({}), 0.0)


class GetTopClassTests(TestCase):
    def test_normal(self):
        pred = _make_prediction(classes=["human", "blank"], scores=[0.991, 0.006])
        name, score = get_top_class(pred)
        self.assertEqual(name, "human")
        self.assertAlmostEqual(score, 0.991)

    def test_taxonomy_normalized(self):
        pred = _make_prediction(classes=["taxonomy;blank"], scores=[0.999])
        name, score = get_top_class(pred)
        self.assertEqual(name, "blank")

    def test_empty(self):
        name, score = get_top_class({})
        self.assertEqual(name, "")
        self.assertEqual(score, 0.0)


# ── Decision matrix tests ────────────────────────────────────────────────────
# should_send_notification returns (bool, reason_str)

class ShouldSendNotificationTests(TestCase):

    def test_aceptacion_directa_animal(self):
        """Animal > 80% → SEND."""
        pred = _make_prediction(
            detections=[{"label": "animal", "conf": 0.85}],
            classes=["blank"], scores=[0.99],
        )
        send, reason = should_send_notification(pred)
        self.assertTrue(send)
        self.assertIn("Aceptación Directa", reason)

    def test_aceptacion_directa_human(self):
        """Human > 80% → SEND."""
        pred = _make_prediction(
            detections=[{"label": "human", "conf": 0.943}, {"label": "vehicle", "conf": 0.875}],
            classes=["human", "blank"], scores=[0.991, 0.006],
        )
        send, reason = should_send_notification(pred)
        self.assertTrue(send)
        self.assertIn("Aceptación Directa", reason)

    def test_conflicto_interesante(self):
        """Detection 50-80% + blank → SEND."""
        pred = _make_prediction(
            detections=[{"label": "animal", "conf": 0.648}],
            classes=["blank", "bird"], scores=[0.974, 0.013],
        )
        send, reason = should_send_notification(pred)
        self.assertTrue(send)
        self.assertIn("Conflicto Interesante", reason)

    def test_clasificacion_segura(self):
        """top ≠ blank with >30% → SEND."""
        pred = _make_prediction(
            detections=[{"label": "animal", "conf": 0.25}],
            classes=["bird", "blank"], scores=[0.65, 0.30],
        )
        send, reason = should_send_notification(pred)
        self.assertTrue(send)
        self.assertIn("Clasificación Segura", reason)

    def test_deteccion_debil_blank(self):
        """Detection < 30% + blank → IGNORE."""
        pred = _make_prediction(
            detections=[{"label": "animal", "conf": 0.15}],
            classes=["blank", "bird"], scores=[0.95, 0.02],
        )
        send, reason = should_send_notification(pred)
        self.assertFalse(send)
        self.assertIn("Detección Débil", reason)

    def test_no_detections_blank(self):
        """No detections + blank → IGNORE."""
        pred = _make_prediction(
            detections=[], classes=["blank"], scores=[0.99],
        )
        send, reason = should_send_notification(pred)
        self.assertFalse(send)

    def test_default_sends(self):
        """Detection 30-50% + blank → default sends by precaution."""
        pred = _make_prediction(
            detections=[{"label": "animal", "conf": 0.35}],
            classes=["blank", "bird"], scores=[0.80, 0.10],
        )
        send, reason = should_send_notification(pred)
        self.assertTrue(send)
        self.assertIn("Default", reason)

    def test_vehicle_only_high(self):
        """Vehicle > 80% → SEND."""
        pred = _make_prediction(
            detections=[{"label": "vehicle", "conf": 0.92}],
            classes=["blank"], scores=[0.95],
        )
        send, reason = should_send_notification(pred)
        self.assertTrue(send)

    def test_taxonomy_blank_filtered(self):
        """SpeciesNet 'taxonomy;blank' + no detections → IGNORE."""
        pred = _make_prediction(
            detections=[],
            classes=["taxonomy;blank", "taxonomy;bird"],
            scores=[0.999, 0.001],
        )
        send, reason = should_send_notification(pred)
        self.assertFalse(send)

    def test_taxonomy_non_blank_sends(self):
        """SpeciesNet taxonomy 'genus;human' at high score → SEND."""
        pred = _make_prediction(
            detections=[{"label": "human", "conf": 0.943}],
            classes=["taxonomy;human", "taxonomy;blank"],
            scores=[0.991, 0.006],
        )
        send, reason = should_send_notification(pred)
        self.assertTrue(send)
