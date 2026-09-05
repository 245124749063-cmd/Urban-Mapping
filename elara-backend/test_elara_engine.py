from models.dummy_ai_engine import ElaraAIEngine


IMAGE_PATH = "test_data/drone_test.jpeg"

engine = ElaraAIEngine()

result = engine.predict(IMAGE_PATH)


print("\n===== ELARA AI ENGINE TEST =====")

print("Status:", result["status"])
print("Task:", result["task"])
print("Classes:", result["classes"])

print("Buildings:", len(result["buildings"]))
print("Edges:", len(result["edges"]))


for building in result["buildings"][:5]:

    print(
        building["id"],
        "confidence=",
        building["confidence"],
        "points=",
        len(building["polygon_pixels"])
    )