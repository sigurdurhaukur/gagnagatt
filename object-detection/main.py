import cv2
from ultralytics import YOLO

# Load the model

cap = cv2.VideoCapture("./road-traffic.mp4")

model = YOLO("yolov8m.pt")


def predict(frame):
    results = model(frame)
    results = results[0]
    bboxes = results.boxes.xyxy.cpu().numpy().astype(int)
    classes = results.boxes.cls.cpu().numpy().astype(int)
    confidences = results.boxes.conf.cpu().numpy()

    return bboxes, classes, confidences


if not cap.isOpened():
    print("Error: Failed to open the video.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    bboxes, classes, confidences = predict(frame)

    for bbox, cls, confidence in zip(bboxes, classes, confidences):
        x1, y1, x2, y2 = bbox
        class_name = model.names[cls]

        # only show if confidence is greater than 0.5
        if confidence < 0.5:
            continue

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 1)
        cv2.putText(
            frame,
            class_name,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )

    cv2.imshow("frame", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
