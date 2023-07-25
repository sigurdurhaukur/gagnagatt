import cv2
from ultralytics import YOLO

cap = cv2.VideoCapture("./iceland-traffic-cleaned.mp4")  # load the video
model = YOLO("yolov8m.pt")  # lode the model


def predict(frame):
    """
    Predicts the bounding boxes, classes, and confidences of the objects in the bottom half of the frame (for performance).
    """
    frame_height, frame_width, _ = frame.shape

    # Crop the frame to analyze only the bottom half
    half_height = frame_height // 2
    bottom_half_frame = frame[half_height:, :, :]

    results = model(bottom_half_frame)
    results = results[0]
    bboxes = results.boxes.xyxy.cpu().numpy().astype(int)
    classes = results.boxes.cls.cpu().numpy().astype(int)
    confidences = results.boxes.conf.cpu().numpy().astype(float)

    # Shift the bounding boxes' y-coordinates to match the original frame
    bboxes[:, [1, 3]] += half_height

    return bboxes, classes, confidences


if not cap.isOpened():
    print("Error: Failed to open the video.")
    exit()

tolerance = 200  # number of frames an object has to be detected in to be counted
detected_objects = {}  # Dictionary to keep track of detected objects

while True:
    ret, frame = cap.read()
    if not ret:
        break

    bboxes, classes, confidences = predict(frame)
    # total number of objects detected

    amount_of_each_class = {}

    for bbox, cls, confidence in zip(bboxes, classes, confidences):
        x1, y1, x2, y2 = bbox
        class_name = model.names[cls]  # type of object detected

        # only show if confidence is greater than 0.5
        if confidence < 0.5:
            continue

        cv2.rectangle(
            frame, (x1, y1), (x2, y2), (0, 255, 0), 1
        )  # draw the bounding box
        cv2.putText(
            frame,
            class_name,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
        )

        if class_name not in detected_objects:
            detected_objects[class_name] = 1
        else:
            detected_objects[class_name] += 1

        # display the object only if it meets the tolerance condition
        if detected_objects[class_name] >= tolerance:
            if class_name not in amount_of_each_class:
                amount_of_each_class[class_name] = 1
            else:
                amount_of_each_class[class_name] += 1

    # display the number of objects detected
    for i, (class_name, amount) in enumerate(amount_of_each_class.items()):
        distance_from_top = 40 * (i + 1)
        cv2.putText(
            frame,
            f"{class_name}: {amount}",
            (10, 30 + distance_from_top),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 0),
            2,
        )

    cv2.imshow("frame", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
