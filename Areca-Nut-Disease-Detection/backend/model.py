"""
CNN Model Integration for Arecanut Disease Detection
Supports Keras 3.x (standalone) + TF 2.16+ backend.
The .h5 file was saved with Keras 3.12.0 / TF backend.
"""

import numpy as np
from PIL import Image
import os
from typing import Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ArecanutDiseaseModel:
    """CNN Model for Arecanut Disease Detection"""

    def __init__(self, model_path: str = "best_arecanut_fast_model.h5"):
        self.model      = None
        self.model_path = model_path
        self.input_size = (224, 224)
        self.is_loaded  = False

        # 9 classes — alphabetical order as Keras assigns indices
        self.disease_classes = {
            0: "healthy_leaf",
            1: "healthy_nut",
            2: "healthy_trunk",
            3: "mahali_koleroga",
            4: "stem_bleeding",
            5: "bud_borer",
            6: "healthy_foot",
            7: "stem_cracking",
            8: "yellow_leaf_disease",
        }

        self.severity_map = {
            "bud_borer":           "high",
            "healthy_foot":        "none",
            "healthy_leaf":        "none",
            "healthy_nut":         "none",
            "healthy_trunk":       "none",
            "mahali_koleroga":     "high",
            "stem_cracking":       "medium",
            "stem_bleeding":       "medium",
            "yellow_leaf_disease": "high",
        }

        self.load_model()

    # ── Model loading ──────────────────────────────────────────────────────

    def load_model(self) -> bool:
        # Resolve path
        if not os.path.exists(self.model_path):
            alt = os.path.join("..", self.model_path)
            if os.path.exists(alt):
                self.model_path = alt
            else:
                logger.warning(f"Model file not found: {self.model_path}")
                return False

        logger.info(f"Loading model from: {self.model_path}")

        # ── Strategy 1: standalone Keras 3 (matches how the file was saved) ──
        try:
            import keras
            logger.info(f"Keras version: {keras.__version__}")
            self.model = keras.saving.load_model(self.model_path, compile=False)
            self._read_input_shape()
            logger.info(f"[OK] Loaded with Keras 3 native loader. Input: {self.input_size}")
            self.is_loaded = True
            return True
        except ImportError:
            logger.warning("Standalone Keras 3 not found, trying tf.keras …")
        except Exception as e:
            logger.warning(f"Keras 3 load failed: {e}")

        # ── Strategy 2: tf.keras (TF 2.16+ ships Keras 3 via tf.keras) ───────
        try:
            import tensorflow as tf
            logger.info(f"TensorFlow version: {tf.__version__}")
            self.model = tf.keras.models.load_model(self.model_path, compile=False)
            self._read_input_shape()
            logger.info(f"[OK] Loaded with tf.keras. Input: {self.input_size}")
            self.is_loaded = True
            return True
        except Exception as e:
            logger.warning(f"tf.keras load failed: {e}")

        # ── Strategy 3: tf.keras with safe_mode disabled ──────────────────────
        try:
            import tensorflow as tf
            self.model = tf.keras.models.load_model(
                self.model_path, compile=False, safe_mode=False
            )
            self._read_input_shape()
            logger.info(f"[OK] Loaded with safe_mode=False. Input: {self.input_size}")
            self.is_loaded = True
            return True
        except Exception as e:
            logger.error(f"All loading strategies failed: {e}")
            return False

    def _read_input_shape(self):
        try:
            shape = self.model.input_shape   # (None, H, W, C)
            if len(shape) == 4:
                self.input_size = (shape[1], shape[2])
        except Exception:
            pass  # keep default 224×224

    # ── Inference ──────────────────────────────────────────────────────────

    def preprocess_image(self, image: Image.Image) -> np.ndarray:
        if image.mode != "RGB":
            image = image.convert("RGB")
        image     = image.resize(self.input_size, Image.LANCZOS)
        img_array = np.array(image, dtype=np.float32) / 255.0
        return np.expand_dims(img_array, axis=0)

    def predict(self, image: Image.Image) -> Dict:
        if not self.is_loaded or self.model is None:
            raise RuntimeError("Model not loaded.")

        processed       = self.preprocess_image(image)
        predictions     = self.model.predict(processed, verbose=0)
        predicted_idx   = int(np.argmax(predictions[0]))
        confidence      = float(predictions[0][predicted_idx])
        disease_key     = self.disease_classes.get(predicted_idx, "unknown")

        top_indices = np.argsort(predictions[0])[-3:][::-1]
        top_predictions = [
            {
                "disease":     self.disease_classes.get(int(i), f"class_{i}"),
                "probability": round(float(predictions[0][i]), 4),
            }
            for i in top_indices
        ]

        return {
            "disease_key":     disease_key,
            "confidence":      round(confidence, 4),
            "severity":        self.severity_map.get(disease_key, "unknown"),
            "top_predictions": top_predictions,
            "model_type":      "CNN (Keras 3)",
        }

    def get_model_info(self) -> Dict:
        if not self.is_loaded:
            return {"status": "not_loaded"}
        return {
            "status":      "loaded",
            "model_path":  self.model_path,
            "input_size":  self.input_size,
            "num_classes": len(self.disease_classes),
            "classes":     list(self.disease_classes.values()),
        }


# ── Singleton ──────────────────────────────────────────────────────────────

_model_instance: Optional[ArecanutDiseaseModel] = None


def get_model() -> ArecanutDiseaseModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = ArecanutDiseaseModel()
    return _model_instance


def is_model_available() -> bool:
    try:
        return get_model().is_loaded
    except Exception:
        return False
