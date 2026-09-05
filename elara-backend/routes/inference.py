from flask import Blueprint, request, jsonify, current_app
from pathlib import Path

from models.dummy_ai_engine import ElaraAIEngine
from utils.geo_processing import (
    convert_ai_predictions_to_geojson,
    check_topology_errors
)


# =========================================================
# BLUEPRINT
# =========================================================

inference_bp = Blueprint("inference", __name__)


# =========================================================
# LOAD AI MODEL ONCE
# =========================================================

ai_engine = ElaraAIEngine()


# =========================================================
# ANALYZE ENDPOINT
# =========================================================

@inference_bp.route("/api/v1/analyze", methods=["POST"])
def run_inference():

    try:

        # -----------------------------------------------------
        # READ REQUEST
        # -----------------------------------------------------

        data = request.get_json(silent=True) or {}

        filepath = data.get("filepath")

        if not filepath:

            return jsonify({
                "status": "error",
                "error": "No filepath provided"
            }), 400


        # -----------------------------------------------------
        # SECURITY CHECK
        # -----------------------------------------------------
        # Make sure the requested file is actually inside
        # ELARA's upload directory.
        # -----------------------------------------------------

        upload_folder = Path(
            current_app.config["UPLOAD_FOLDER"]
        ).resolve()

        requested_file = Path(filepath).resolve()

        try:

            requested_file.relative_to(
                upload_folder
            )

        except ValueError:

            return jsonify({
                "status": "error",
                "error": "Invalid file path"
            }), 400


        # -----------------------------------------------------
        # CHECK FILE EXISTS
        # -----------------------------------------------------

        if not requested_file.exists():

            return jsonify({
                "status": "error",
                "error": "Uploaded file not found"
            }), 404


        # =====================================================
        # STEP 1 — YOLO AI INFERENCE
        # =====================================================

        print("\n===== ELARA AI INFERENCE =====")

        predictions = ai_engine.predict(
            str(requested_file)
        )


        # =====================================================
        # STEP 2 — EXTRACT AI RESULTS
        # =====================================================

        buildings = predictions.get(
            "buildings",
            []
        )

        edges = predictions.get(
            "edges",
            []
        )

        roads = predictions.get(
            "roads",
            []
        )

        all_detections = predictions.get(
            "detections",
            []
        )


        # =====================================================
        # STEP 3 — CALCULATE AVERAGE CONFIDENCE
        # =====================================================

        if all_detections:

            overall_confidence = (
                sum(
                    item["confidence"]
                    for item in all_detections
                )
                /
                len(all_detections)
            )

        else:

            overall_confidence = 0.0


        # =====================================================
        # STEP 4 — CONVERT AI OUTPUT TO GEOJSON
        # =====================================================

        geojson = convert_ai_predictions_to_geojson(
            predictions
        )


        # =====================================================
        # STEP 5 — TOPOLOGY / QC CHECK
        # =====================================================

        qc_anomalies = check_topology_errors(
            geojson.get("features", [])
        )


        # =====================================================
        # STEP 6 — PRINT PROCESSING SUMMARY
        # =====================================================

        print(
            "Buildings:",
            len(buildings)
        )

        print(
            "Edges:",
            len(edges)
        )

        print(
            "Roads:",
            len(roads)
        )

        print(
            "Total detections:",
            len(all_detections)
        )

        print(
            "Average confidence:",
            round(
                overall_confidence,
                4
            )
        )

        print(
            "GeoJSON features:",
            len(
                geojson.get(
                    "features",
                    []
                )
            )
        )

        print(
            "QC anomalies:",
            len(qc_anomalies)
        )


        # =====================================================
        # STEP 7 — RETURN COMPLETE ELARA RESULT
        # =====================================================

        return jsonify({

            "status": "processed",

            "task": predictions.get(
                "task"
            ),

            "classes": predictions.get(
                "classes"
            ),

            # -------------------------------------------------
            # SUMMARY
            # -------------------------------------------------

            "summary": {

                "buildings": len(
                    buildings
                ),

                "edges": len(
                    edges
                ),

                "roads": len(
                    roads
                ),

                "total_detections": len(
                    all_detections
                ),

                "overall_confidence": round(
                    overall_confidence,
                    4
                ),

                "geojson_features": len(
                    geojson.get(
                        "features",
                        []
                    )
                ),

                "qc_anomalies": len(
                    qc_anomalies
                )
            },


            # -------------------------------------------------
            # GEOJSON
            # -------------------------------------------------

            "geojson": geojson,


            # -------------------------------------------------
            # QUALITY CONTROL
            # -------------------------------------------------

            "quality_control": {

                "status": (
                    "issues_found"
                    if qc_anomalies
                    else "passed"
                ),

                "total_anomalies": len(
                    qc_anomalies
                ),

                "anomalies": qc_anomalies
            },


            # -------------------------------------------------
            # RAW AI RESULTS
            # -------------------------------------------------

            "features": predictions

        }), 200


    # =========================================================
    # FILE NOT FOUND
    # =========================================================

    except FileNotFoundError as e:

        return jsonify({

            "status": "error",

            "error": str(e)

        }), 404


    # =========================================================
    # GENERAL ERROR
    # =========================================================

    except Exception as e:

        return jsonify({

            "status": "error",

            "error": "ELARA inference failed",

            "details": str(e)

        }), 500