from shapely.geometry import Polygon, MultiPolygon, mapping
from shapely.validation import explain_validity


# =========================================================
# CREATE SHAPELY POLYGON
# =========================================================

def pixel_polygon_to_shapely(points):
    """
    Convert YOLO pixel-coordinate points into a Shapely Polygon.
    """

    if not points or len(points) < 3:
        return None

    try:
        polygon = Polygon(points)

        if polygon.is_empty:
            return None

        return polygon

    except Exception:
        return None


# =========================================================
# AUTO-SANITIZE GEOMETRY
# =========================================================

def sanitize_polygon(geometry):
    """
    Repair common invalid polygon geometries.

    buffer(0) can repair self-intersections.
    The result may be a Polygon OR MultiPolygon.
    """

    if geometry is None:
        return None, False

    # Already valid
    if geometry.is_valid:
        return geometry, False

    try:
        repaired = geometry.buffer(0)

        if repaired.is_empty:
            return None, False

        if repaired.is_valid:
            return repaired, True

    except Exception:
        pass

    return None, False


# =========================================================
# CONVERT SHAPELY GEOMETRY TO GEOJSON
# =========================================================

def shapely_to_geojson_geometry(geometry):
    """
    Convert Polygon or MultiPolygon into valid GeoJSON geometry.
    """

    if geometry is None or geometry.is_empty:
        return None

    if geometry.geom_type not in [
        "Polygon",
        "MultiPolygon"
    ]:
        return None

    return mapping(geometry)


# =========================================================
# CONVERT AI PREDICTIONS TO GEOJSON
# =========================================================

def convert_ai_predictions_to_geojson(predictions):
    """
    Convert ELARA YOLO predictions into a GeoJSON
    FeatureCollection.

    Current JPEG/PNG inputs have no geographic CRS,
    so coordinates remain in pixel space.
    """

    features = []

    # =====================================================
    # BUILDINGS
    # =====================================================

    for item in predictions.get("buildings", []):

        raw_polygon = pixel_polygon_to_shapely(
            item.get("polygon_pixels", [])
        )

        if raw_polygon is None:
            continue

        polygon, was_repaired = sanitize_polygon(
            raw_polygon
        )

        if polygon is None:
            continue

        geometry = shapely_to_geojson_geometry(
            polygon
        )

        if geometry is None:
            continue

        features.append({

            "type": "Feature",

            "properties": {

                "id": item.get(
                    "id",
                    "BUILDING"
                ),

                "type": "building",

                "class_id": item.get(
                    "class_id"
                ),

                "confidence": item.get(
                    "confidence",
                    0.0
                ),

                "coordinate_system": "pixel",

                "geometry_valid": polygon.is_valid,

                "geometry_repaired": was_repaired
            },

            "geometry": geometry
        })

    # =====================================================
    # EDGES
    # =====================================================

    for item in predictions.get("edges", []):

        raw_polygon = pixel_polygon_to_shapely(
            item.get("polygon_pixels", [])
        )

        if raw_polygon is None:
            continue

        polygon, was_repaired = sanitize_polygon(
            raw_polygon
        )

        if polygon is None:
            continue

        geometry = shapely_to_geojson_geometry(
            polygon
        )

        if geometry is None:
            continue

        features.append({

            "type": "Feature",

            "properties": {

                "id": item.get(
                    "id",
                    "EDGE"
                ),

                "type": "edge",

                "class_id": item.get(
                    "class_id"
                ),

                "confidence": item.get(
                    "confidence",
                    0.0
                ),

                "coordinate_system": "pixel",

                "geometry_valid": polygon.is_valid,

                "geometry_repaired": was_repaired
            },

            "geometry": geometry
        })

    # =====================================================
    # RETURN FEATURE COLLECTION
    # =====================================================

    return {

        "type": "FeatureCollection",

        "features": features
    }


# =========================================================
# TOPOLOGY / QC ENGINE
# =========================================================

def check_topology_errors(features):
    """
    Perform topology and geometry quality checks.

    Checks:
        1. Missing geometry
        2. Invalid geometry
        3. Empty geometry
        4. Polygon overlaps

    Current coordinates are in pixel space.
    """

    anomalies = []

    polygons = []

    # =====================================================
    # FEATURE VALIDATION
    # =====================================================

    for index, feature in enumerate(features):

        properties = feature.get(
            "properties",
            {}
        )

        geometry = feature.get(
            "geometry"
        )

        feature_id = properties.get(
            "id",
            f"FEATURE-{index + 1}"
        )

        # -------------------------------------------------
        # MISSING GEOMETRY
        # -------------------------------------------------

        if not geometry:

            anomalies.append({

                "type": "Missing Geometry",

                "severity": "Critical",

                "feature_id": feature_id,

                "description":
                    "Feature does not contain geometry."
            })

            continue

        # -------------------------------------------------
        # CONVERT GEOJSON TO SHAPELY
        # -------------------------------------------------

        try:

            geometry_type = geometry.get(
                "type"
            )

            coordinates = geometry.get(
                "coordinates"
            )

            if geometry_type == "Polygon":

                polygon = Polygon(
                    coordinates[0]
                )

            elif geometry_type == "MultiPolygon":

                polygon = MultiPolygon([
                    Polygon(
                        polygon_coordinates[0]
                    )

                    for polygon_coordinates
                    in coordinates
                ])

            else:

                polygon = None

        except Exception:

            polygon = None

        # -------------------------------------------------
        # INVALID GEOMETRY
        # -------------------------------------------------

        if polygon is None:

            anomalies.append({

                "type": "Invalid Geometry",

                "severity": "High",

                "feature_id": feature_id,

                "description":
                    "Unable to construct a valid polygon."
            })

            continue

        # -------------------------------------------------
        # EMPTY GEOMETRY
        # -------------------------------------------------

        if polygon.is_empty:

            anomalies.append({

                "type": "Empty Geometry",

                "severity": "High",

                "feature_id": feature_id,

                "description":
                    "Geometry contains no usable coordinates."
            })

            continue

        # -------------------------------------------------
        # VALIDITY CHECK
        # -------------------------------------------------

        if not polygon.is_valid:

            anomalies.append({

                "type": "Invalid Geometry",

                "severity": "High",

                "feature_id": feature_id,

                "description":
                    explain_validity(polygon)
            })

        # -------------------------------------------------
        # STORE POLYGONS FOR OVERLAP CHECK
        # -------------------------------------------------

        if properties.get("type") in [
            "parcel",
            "edge"
        ]:

            polygons.append(
                (
                    feature_id,
                    polygon
                )
            )

    # =====================================================
    # OVERLAP CHECK
    # =====================================================

    for i in range(
        len(polygons)
    ):

        id1, polygon1 = polygons[i]

        for j in range(
            i + 1,
            len(polygons)
        ):

            id2, polygon2 = polygons[j]

            if not polygon1.intersects(
                polygon2
            ):
                continue

            try:

                intersection = (
                    polygon1.intersection(
                        polygon2
                    )
                )

            except Exception:

                continue

            if intersection.is_empty:
                continue

            if intersection.area > 0:

                anomalies.append({

                    "type":
                        "Polygon Overlap",

                    "severity":
                        "High",

                    "feature_id":
                        id1,

                    "related_feature":
                        id2,

                    "description": (
                        f"{id1} overlaps "
                        f"{id2} by approximately "
                        f"{round(intersection.area, 2)} "
                        f"pixel²."
                    ),

                    "coordinates": [

                        float(
                            intersection.centroid.x
                        ),

                        float(
                            intersection.centroid.y
                        )
                    ]
                })

    return anomalies