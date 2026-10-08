import os
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_call_stack_level"] = "1"
import re
import cv2
import numpy as np
import threading
from paddleocr import PaddleOCR

OCR_INFERENCE_LOCK = threading.Lock()
NOISE_TOKENS = {"IND", "IN", "INDIA"}


class OCRReader:
    def __init__(self):
        try:
            self.ocr = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=True,
                lang="en",
            )
        except Exception as e:
            raise RuntimeError(f"PaddleOCR failed to initialize: {e}")

    def _load_image(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            try:
                from PIL import Image
                pil_img = Image.open(image_path).convert("RGB")
                image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception as e:
                raise RuntimeError(f"Could not load image {image_path}: {e}")
        return image

    def _preprocess(self, image):
        h, w = image.shape[:2]
        min_width = 300
        if w < min_width:
            scale = min_width / max(w, 1)
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        return image

    def _parse_results(self, results):
        pairs = []
        if not results:
            return pairs
        for res in results:
            if hasattr(res, "get"):
                texts = res.get("rec_texts", []) or []
                scores = res.get("rec_scores", []) or []
            else:
                texts = getattr(res, "rec_texts", []) or []
                scores = getattr(res, "rec_scores", []) or []
            for text, conf in zip(texts, scores):
                pairs.append((text, conf))
        return pairs

    def extract_text(self, image, min_conf=0.35):
        try:
            if image is None or image.size == 0:
                return {"plate_text": None, "message": "No image provided"}

            image = self._preprocess(image)
            with OCR_INFERENCE_LOCK:
                results = self.ocr.predict(image)

            pairs = self._parse_results(results)
            texts = [text for text, conf in pairs if conf >= min_conf]
            texts = [t for t in texts if t.strip().upper() not in NOISE_TOKENS]

            if not texts:
                return {"plate_text": None, "message": "Plate not readable"}

            plate_number = re.sub(r"[^A-Z0-9]", "", " ".join(texts).upper())
            if len(plate_number) < 6:
                return {"plate_text": None, "message": "Invalid plate"}

            kept_confs = [
                conf for text, conf in pairs
                if conf >= min_conf and text.strip().upper() not in NOISE_TOKENS
            ]
            avg_conf = sum(kept_confs) / len(kept_confs) if kept_confs else min_conf
            return {"plate_text": plate_number, "confidence": avg_conf, "message": "Success"}
        except Exception as e:
            raise RuntimeError(f"OCR processing failed: {e}")
