from pathlib import Path
from ultralytics import YOLO


class ElaraAIEngine:
    def __init__(self, model_weights_path=None):

        # ---------------------------------------------------------
        # LOAD MODEL WEIGHTS
        # ---------------------------------------------------------

        if model_weights_path is None:
            model_weights_path = (
                Path(__file__).parent / "weights" / "best.pt"
            )

        self.model_weights_path = Path(model_weights_path)

        if not self.model_weights_path.exists():
            raise FileNotFoundError(
                f"YOLO model not found: {self.model_weights_path}"
            )

        # Load YOLO model
        self.model = YOLO(str(self.model_weights_path))

        print("ELARA AI MODEL LOADED")
        print("Task:", self.model.task)
        print("Classes:", self.model.names)

    # ---------------------------------------------------------
    # PREDICTION
    # ---------------------------------------------------------

    def predict(self, raster_path):
        """
        Run YOLO segmentation on an input aerial image.

        The YOLO model returns segmentation polygons in
        PIXEL coordinates.

        Geographic conversion will be handled separately
        by the GIS processing layer.
        """

        image_path = Path(raster_path)

        # -----------------------------------------------------
        # CHECK INPUT IMAGE
        # -----------------------------------------------------

        if not image_path.exists():
            raise FileNotFoundError(
                f"Input image not found: {image_path}"
            )

        # -----------------------------------------------------
        # RUN YOLO SEGMENTATION
        # -----------------------------------------------------

        results = self.model.predict(
            source=str(image_path),
            conf=0.25,
            verbose=False
        )

        result = results[0]

        # -----------------------------------------------------
        # INITIAL OUTPUT STRUCTURE
        # -----------------------------------------------------

        features = {
            "status": "success",
            "image": str(image_path),
            "task": self.model.task,
            "classes": self.model.names,

            # AI feature categories
            "buildings": [],
            "edges": [],
            "roads": [],

            # All detections
            "detections": []
        }

        # -----------------------------------------------------
        # NO DETECTIONS
        # -----------------------------------------------------

        if result.boxes is None or result.masks is None:
            return features

        # -----------------------------------------------------
        # PROCESS EACH DETECTION
        # -----------------------------------------------------

        for i in range(len(result.boxes)):

            # Class ID
            class_id = int(
                result.boxes.cls[i]
            )

            # Confidence score
            confidence = float(
                result.boxes.conf[i]
            )

            # Class name
            class_name = self.model.names[class_id]

            # -------------------------------------------------
            # SEGMENTATION POLYGON
            # -------------------------------------------------
            # YOLO returns polygon points as:
            #
            # [(x1, y1), (x2, y2), ...]
            #
            # These are PIXEL coordinates.
            # -------------------------------------------------

            polygon = result.masks.xy[i].tolist()

            # -------------------------------------------------
            # CREATE DETECTION OBJECT
            # -------------------------------------------------

            detection = {
                "id": f"{class_name.upper()}-{i + 1:04d}",
                "class_id": class_id,
                "class_name": class_name,
                "confidence": round(confidence, 4),
                "polygon_pixels": polygon
            }

            # Add to all detections
            features["detections"].append(
                detection
            )

            # -------------------------------------------------
            # CLASSIFICATION
            # -------------------------------------------------

            if class_name == "building":

                features["buildings"].append(
                    detection
                )

            elif class_name == "edge":

                features["edges"].append({
                    **detection,
                    "type": "edge"
                })

            # -------------------------------------------------
            # FUTURE ROAD CLASS
            # -------------------------------------------------
            # Your current model does not have a road class.
            # This is reserved for future model versions.
            # -------------------------------------------------

            elif class_name == "road":

                features["roads"].append(
                    detection
                )

        # -----------------------------------------------------
        # RETURN AI RESULTS
        # -----------------------------------------------------

        return features