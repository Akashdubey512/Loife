"""
reServe AI - Computer Vision Quality Intelligence Pipeline

⚠ SIMULATION MODE ⚠
No trained model weights are loaded. This module returns simulated freshness
scores using a random number generator to stand in for real CNN inference.

In a production deployment this would be replaced by a PyTorch / ONNX
EfficientNet-B0 model loaded from a checkpoint file. Until that artifact
is available and verified, all inference results MUST be treated as
SIMULATED and require mandatory human inspector sign-off before any food
batch is cleared for redistribution.

Dataset benchmark referenced in design: Kaggle Fresh and Rotten Fruits &
Vegetables Dataset (classification labels only; no pre-trained weights are
included in this repository).
"""

import random
from typing import Dict, Any


SIMULATION_MODE = True
SIMULATION_NOTICE = (
    "SIMULATED — No trained model weights loaded. "
    "Human inspector sign-off is mandatory before redistribution."
)


class FreshnessClassificationPipeline:
    """
    Wrapper around the (currently simulated) CV freshness classification step.

    When SIMULATION_MODE is True:
      - Scores are random values in a realistic range.
      - Always returns FRESH because the random range is 89–98 (above all
        degradation thresholds). This is a known limitation that makes
        simulation results unreliable as safety indicators.
      - The 'simulated' flag in the response is always True.

    When a real model checkpoint is loaded and verified:
      - Set SIMULATION_MODE = False.
      - Replace _simulated_infer() with real torch/onnx forward pass.
      - Remove the simulation disclaimer from response payloads.
    """

    def __init__(self, model_name: str = "EfficientNet-B0"):
        self.model_name = model_name
        self.classes = ["FRESH", "MODERATE", "DEGRADING", "ROTTEN"]
        self.status_mapping = {
            "FRESH":     "SAFE_FOR_REDISTRIBUTION",
            "MODERATE":  "PROCESS_IMMEDIATELY",
            "DEGRADING": "COMPOST_ONLY",
            "ROTTEN":    "HAZARD_DISCARD",
        }

    def preprocess_image(self, image_bytes: bytes) -> Dict[str, Any]:
        """Placeholder: would resize to 224×224 and normalise in real deployment."""
        return {
            "size_bytes": len(image_bytes),
            "target_resolution": [224, 224, 3],
            "normalized": True,
        }

    def _simulated_infer(self) -> Dict[str, Any]:
        """
        Returns a random score in the 89–98 range.
        KNOWN LIMITATION: this range always resolves to FRESH. The simulation
        does not exercise the MODERATE / DEGRADING / ROTTEN branches of the
        classification logic at runtime.
        """
        score = round(random.uniform(89.0, 98.2), 1)
        # Classification thresholds
        if score < 40:
            level = "ROTTEN"
            remaining_days = 0.2
        elif score < 65:
            level = "DEGRADING"
            remaining_days = 0.8
        elif score < 85:
            level = "MODERATE"
            remaining_days = 1.8
        else:
            level = "FRESH"
            remaining_days = round((score / 100.0) * 5.0, 1)

        return {
            "freshness_level": level,
            "quality_score": score,
            "remaining_days": remaining_days,
            "confidence": 0.965,          # placeholder — not from a real model
            "defects_detected": [] if level == "FRESH" else ["Minor Surface Softening"],
        }

    def infer(self, image_bytes: bytes, food_name: str = "Produce") -> Dict[str, Any]:
        """
        Entry point called by the quality router.
        Always sets simulated=True and includes the simulation notice so that
        downstream callers and the API response can surface this to users.
        """
        self.preprocess_image(image_bytes)  # validate bytes are readable

        result = self._simulated_infer()
        level  = result["freshness_level"]
        status = self.status_mapping[level]

        return {
            "food_type":             food_name,
            "freshness_level":       level,
            "quality_score":         result["quality_score"],
            "remaining_days":        result["remaining_days"],
            "redistribution_status": status,
            "model_architecture":    f"{self.model_name} (SIMULATED — no weights loaded)",
            "confidence":            result["confidence"],
            "defects_detected":      result["defects_detected"],
            "simulated":             SIMULATION_MODE,
            "simulation_notice":     SIMULATION_NOTICE if SIMULATION_MODE else None,
        }


cv_pipeline = FreshnessClassificationPipeline()
