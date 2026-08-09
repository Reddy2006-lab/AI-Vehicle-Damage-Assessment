from ultralytics import YOLO

# Load YOLO model
model = YOLO("yolo11n.pt")

# Analyze the vehicle image
results = model(r"uploads\car.jpg")

# Display results
for result in results:
    result.show()

print("YOLO test completed successfully!")
