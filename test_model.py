from ultralytics import YOLO
from pathlib import Path

model_path = Path("best.pt")

if not model_path.exists():
    print("ERROR: best.pt file not found!")
else:
    model = YOLO(str(model_path))

    print("Model loaded successfully!")
    print("Model classes:", model.names)

    image_path = input("Enter your road image path: ").strip().strip('"')

    if not Path(image_path).exists():
        print("ERROR: Image file not found!")
    else:
        results = model.predict(
            source=image_path,
            conf=0.25,
            save=True
        )

        for result in results:
            print("Detected objects:", len(result.boxes))

            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                print(
                    f"Class: {model.names[class_id]}, "
                    f"Confidence: {confidence:.2f}"
                )

        print("Test completed!")