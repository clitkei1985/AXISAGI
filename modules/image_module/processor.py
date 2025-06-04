import os
import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Optional, Tuple, BinaryIO
from datetime import datetime
from pathlib import Path
import logging
from ultralytics import YOLO
import torch
from core.config import settings

logger = logging.getLogger(__name__)

class ImageProcessor:
    def __init__(self):
        self.max_image_size = settings.image.max_image_size
        self.supported_formats = settings.image.supported_formats
        
        # Initialize YOLO model if path is configured
        self.yolo_model = None
        if settings.image.yolo_model_path:
            try:
                self.yolo_model = YOLO(settings.image.yolo_model_path)
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")

    async def process_image(
        self,
        file: BinaryIO,
        operations: Dict[str, any]
    ) -> Tuple[str, Dict]:
        """Process image with specified operations."""
        try:
            # Read image
            image = Image.open(file)
            
            # Check format
            if image.format.lower() not in self.supported_formats:
                raise ValueError(f"Unsupported image format: {image.format}")
            
            # Check size
            if max(image.size) > self.max_image_size:
                ratio = self.max_image_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.LANCZOS)
            
            # Apply operations
            metadata = {}
            
            if operations.get("resize"):
                width, height = operations["resize"]
                image = image.resize((width, height), Image.LANCZOS)
                metadata["resize"] = {"width": width, "height": height}
            
            if operations.get("rotate"):
                angle = operations["rotate"]
                image = image.rotate(angle, expand=True)
                metadata["rotate"] = angle
            
            if operations.get("filters"):
                for filter_name in operations["filters"]:
                    if filter_name == "grayscale":
                        image = image.convert("L")
                    elif filter_name == "blur":
                        image = image.filter(ImageFilter.BLUR)
                    # Add more filters as needed
                metadata["filters"] = operations["filters"]
            
            # Save processed image
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_path = Path("uploads/images") / f"processed_{timestamp}.{image.format.lower()}"
            image.save(output_path)
            
            return str(output_path), metadata
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            raise

    async def detect_objects(
        self,
        file: BinaryIO,
        confidence: float = 0.5
    ) -> List[Dict]:
        """Detect objects in image using YOLO."""
        if not self.yolo_model:
            raise ValueError("YOLO model not available")
        
        try:
            # Save temporary file for YOLO
            temp_path = Path("uploads/images/temp.jpg")
            with open(temp_path, "wb") as f:
                f.write(file.read())
            
            # Run detection
            results = self.yolo_model(str(temp_path))[0]
            
            # Process results
            detections = []
            for box in results.boxes:
                if box.conf[0] >= confidence:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    class_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    
                    detections.append({
                        "class": results.names[class_id],
                        "confidence": conf,
                        "bbox": {
                            "x1": int(x1),
                            "y1": int(y1),
                            "x2": int(x2),
                            "y2": int(y2)
                        }
                    })
            
            # Cleanup
            os.remove(temp_path)
            
            return detections
            
        except Exception as e:
            logger.error(f"Object detection error: {e}")
            raise

    async def extract_features(
        self,
        file: BinaryIO
    ) -> Dict:
        """Extract image features for analysis."""
        try:
            # Read image
            image = Image.open(file)
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Basic features
            features = {
                "size": {
                    "width": image.size[0],
                    "height": image.size[1]
                },
                "format": image.format,
                "mode": image.mode,
                "histogram": {
                    channel: cv2.calcHist([cv_image], [i], None, [256], [0, 256]).flatten().tolist()
                    for i, channel in enumerate(['blue', 'green', 'red'])
                }
            }
            
            # Color statistics
            colors = np.array(image).reshape(-1, 3)
            features["color_stats"] = {
                "mean": colors.mean(axis=0).tolist(),
                "std": colors.std(axis=0).tolist(),
                "dominant": self._get_dominant_colors(colors, k=5)
            }
            
            # Edge detection
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            features["edge_density"] = (edges > 0).mean()
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction error: {e}")
            raise

    def _get_dominant_colors(
        self,
        colors: np.ndarray,
        k: int = 5
    ) -> List[List[int]]:
        """Get dominant colors using k-means clustering."""
        colors = colors.astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        _, labels, centers = cv2.kmeans(colors, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Sort by cluster size
        unique_labels, counts = np.unique(labels, return_counts=True)
        sorted_indices = np.argsort(counts)[::-1]
        
        return [centers[i].astype(int).tolist() for i in sorted_indices]

    async def compare_images(
        self,
        image1: BinaryIO,
        image2: BinaryIO
    ) -> Dict:
        """Compare two images and compute similarity metrics."""
        try:
            # Read images
            img1 = Image.open(image1)
            img2 = Image.open(image2)
            
            # Resize to same size for comparison
            size = (min(img1.size[0], img2.size[0]), min(img1.size[1], img2.size[1]))
            img1 = img1.resize(size)
            img2 = img2.resize(size)
            
            # Convert to numpy arrays
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            # Compute metrics
            mse = np.mean((arr1 - arr2) ** 2)
            psnr = 20 * np.log10(255 / np.sqrt(mse)) if mse > 0 else float('inf')
            
            # Compute histogram similarity
            hist1 = cv2.calcHist([arr1], [0], None, [256], [0, 256])
            hist2 = cv2.calcHist([arr2], [0], None, [256], [0, 256])
            hist_sim = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            
            return {
                "mse": float(mse),
                "psnr": float(psnr),
                "histogram_similarity": float(hist_sim),
                "size_difference": {
                    "width": img1.size[0] - img2.size[0],
                    "height": img1.size[1] - img2.size[1]
                }
            }
            
        except Exception as e:
            logger.error(f"Image comparison error: {e}")
            raise

# Singleton instance
_image_processor = None

def get_image_processor() -> ImageProcessor:
    """Get or create the ImageProcessor singleton instance."""
    global _image_processor
    if _image_processor is None:
        _image_processor = ImageProcessor()
    return _image_processor 