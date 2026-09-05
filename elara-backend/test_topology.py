from utils.geo_processing import check_topology_errors


# =========================================================
# CREATE TWO INTENTIONALLY OVERLAPPING POLYGONS
# =========================================================

test_features = [

    {
        "type": "Feature",

        "properties": {
            "id": "EDGE-0001",
            "type": "edge"
        },

        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [100, 100],
                [300, 100],
                [300, 300],
                [100, 300],
                [100, 100]
            ]]
        }
    },

    {
        "type": "Feature",

        "properties": {
            "id": "EDGE-0002",
            "type": "edge"
        },

        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [200, 200],
                [400, 200],
                [400, 400],
                [200, 400],
                [200, 200]
            ]]
        }
    }
]


# =========================================================
# RUN ELARA QC ENGINE
# =========================================================

print("\n===== ELARA TOPOLOGY QC TEST =====")

errors = check_topology_errors(test_features)


# =========================================================
# DISPLAY RESULTS
# =========================================================

print("Total anomalies:", len(errors))


for index, error in enumerate(errors, start=1):

    print(f"\n--- ANOMALY {index} ---")

    print("Type:", error.get("type"))
    print("Severity:", error.get("severity"))
    print("Feature:", error.get("feature_id"))
    print("Related:", error.get("related_feature"))
    print("Description:", error.get("description"))


# =========================================================
# FINAL RESULT
# =========================================================

if errors:

    print("\n✅ TOPOLOGY QC TEST PASSED")
    print("ELARA successfully detected the intentional overlap.")

else:

    print("\n❌ TOPOLOGY QC TEST FAILED")
    print("ELARA did not detect the overlap.")