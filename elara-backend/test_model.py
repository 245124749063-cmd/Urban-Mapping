from ultralytics import YOLO

MODEL_PATH = "elara-backend/models/weights/best.pt"
IMAGE_PATH = "elara-backend/test_data/drone_test.jpeg"
model = YOLO(MODEL_PATH)

results = model.predict(
    source=IMAGE_PATH,
    conf=0.25,
    save=True,
    verbose=True
)

result = results[0]

print("\n===== ELARA MODEL TEST =====")
print("Task:", model.task)
print("Classes:", model.names)

if result.masks is not None:
    print("Number of masks:", len(result.masks))
    print("Mask shape:", result.masks.data.shape)
else:
    print("No segmentation masks found.")

if result.boxes is not None:
    print("Number of detections:", len(result.boxes))

    for i, cls in enumerate(result.boxes.cls):
        class_id = int(cls)
        confidence = float(result.boxes.conf[i])

        print(
            f"{i + 1}: "
            f"{model.names[class_id]} "
            f"confidence={confidence:.3f}"
        )