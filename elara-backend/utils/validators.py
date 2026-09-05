import os
import rasterio
from shapely.geometry import shape
from werkzeug.utils import secure_filename

# Allowed GIS image formats for ELARA
ALLOWED_RASTER_EXTENSIONS = {'tif', 'tiff', 'png', 'jpg', 'jpeg'}
ALLOWED_RASTER_MIME_TYPES = {'image/tiff', 'image/png', 'image/jpeg', 'image/x-tiff'}

def is_allowed_file(filename: str) -> bool:
    """
    Validates if the uploaded file has an acceptable extension.
    """
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_RASTER_EXTENSIONS


def validate_raster_file(filepath: str) -> dict:
    """
    Inspects uploaded GeoTIFF or aerial orthophoto using rasterio.
    Checks spatial bounds, coordinate system, band counts, and resolution.
    """
    if not os.path.exists(filepath):
        return {"valid": False, "error": "File does not exist on server"}

    try:
        with rasterio.open(filepath) as dataset:
            crs = dataset.crs.to_string() if dataset.crs else "Unknown/Unprojected"
            bounds = dataset.bounds
            width = dataset.width
            height = dataset.height
            count = dataset.count
            
            # Estimate Spatial Resolution (GSD) if georeferenced
            transform = dataset.transform
            gsd_x = abs(transform[0])
            gsd_y = abs(transform[4])

            return {
                "valid": True,
                "crs": crs,
                "dimensions": {"width": width, "height": height, "bands": count},
                "bounds": {
                    "left": bounds.left,
                    "bottom": bounds.bottom,
                    "right": bounds.right,
                    "top": bounds.top
                },
                "resolution": {"gsd_x": gsd_x, "gsd_y": gsd_y}
            }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Invalid or corrupted raster file: {str(e)}"
        }


def validate_geojson_schema(data: dict) -> tuple[bool, str]:
    """
    Validates if incoming JSON is a structurally sound GeoJSON FeatureCollection.
    """
    if not isinstance(data, dict):
        return False, "Payload must be a JSON object"

    if data.get("type") != "FeatureCollection":
        return False, "GeoJSON root type must be 'FeatureCollection'"

    features = data.get("features")
    if not isinstance(features, list):