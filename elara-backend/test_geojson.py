from models.dummy_ai_engine import ElaraAIEngine
from utils.geo_processing import convert_ai_predictions_to_geojson
import json


# ---------------------------------------------------------
# TEST IMAGE
# ---------------------------------------------------------

IMAGE_PATH = "test_data/drone_test.jpeg"


# ---------------------------------------------------------
# LOAD AI ENGINE
# ---------------------------------------------------------

engine = ElaraAIEngine()


# ---------------------------------------------------------
# RUN YOLO
# ---------------------------------------------------------

predictions = engine.predict(IMAGE_PATH)


# ---------------------------------------------------------
# CONVERT AI OUTPUT TO GEOJSON
# ---------------------------------------------------------

geojson = convert_ai_predictions_to_geojson(predictions)


# ---------------------------------------------------------
# PRINT RESULTS
# ---------------------------------------------------------

print("\n===== ELARA GEOJSON TEST =====")

print("GeoJSON Type:", geojson["type"])

print(
    "Total Features:",
    len(geojson["features"])
)


# ---------------------------------------------------------
# SHOW FIRST FEATURE
# ---------------------------------------------------------

if geojson["features"]:

    first_feature = geojson["features"][0]

    print("\n===== FIRST FEATURE =====")

    print(
        json.dumps(
            first_feature,
            indent=2
        )
    )

else:

    print("\nNo features were generated.")


# ---------------------------------------------------------
# SAVE GEOJSON
# ---------------------------------------------------------

output_file = "test_output.geojson"

with open(
    output_file,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        geojson,
        f,
        indent=2
    )


print(
    f"\nGeoJSON saved to: {output_file}"
)

print("\n===== TEST COMPLETE =====")