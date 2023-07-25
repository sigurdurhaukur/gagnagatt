import cv2
from ultralytics import YOLO
import numpy as np


class ObjectDetector:
    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def predict(self, frame):
        """
        Predicts the bounding boxes, classes, and confidences of the objects in the bottom half of the frame (for performance).
        """
        frame_height, frame_width, _ = frame.shape

        # Crop the frame to analyze only the bottom half
        half_height = frame_height // 2
        bottom_half_frame = frame[half_height:, :, :]

        results = self.model(bottom_half_frame)
        results = results[0]
        bboxes = results.boxes.xyxy.cpu().numpy().astype(int)
        classes = results.boxes.cls.cpu().numpy().astype(int)
        confidences = results.boxes.conf.cpu().numpy().astype(float)

        # Shift the bounding boxes' y-coordinates to match the original frame
        bboxes[:, [1, 3]] += half_height

        return bboxes, classes, confidences


class VideoProcessor:
    def __init__(self, video_path, model_path, tolerance):
        self.cap = cv2.VideoCapture(video_path)
        self.detector = ObjectDetector(model_path)
        self.tolerance = tolerance
        self.detected_objects = {}
        self.model = YOLO(model_path)

    def draw_bounding_boxes(
        self,
        frame,
        bboxes,
        classes,
        confidences,
        amount_of_each_class,
        color=(0, 255, 0),
        area_width=100,
        area_height=100,
        end_area_top_left=(404 - 100, 900),
        start_area_top_left=(1120, 815),
    ):
        for bbox, cls, confidence in zip(bboxes, classes, confidences):
            x1, y1, x2, y2 = bbox
            class_name = self.model.names[cls]  # type of object detected

            # only show if confidence is greater than 0.5
            if confidence < 0.5:
                continue

            # draw the bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1)
            # display the class name
            cv2.putText(
                frame,
                class_name,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                1,
            )

            # draw the midpoint of the bounding box
            midpoint_x = (x1 + x2) // 2
            midpoint_y = (y1 + y2) // 2

            cv2.circle(
                frame,
                (midpoint_x, midpoint_y),
                5,
                color,
                -1,
            )

            # check if the midpoint is inside the start area
            if self.is_point_inside_rectangle(
                midpoint_x,
                midpoint_y,
                start_area_top_left[0],
                start_area_top_left[1],
                area_width,
                area_height,
            ):
                pass  # TODO: implement

            if class_name not in self.detected_objects:
                self.detected_objects[class_name] = 1
            else:
                self.detected_objects[class_name] += 1

            # display the object only if it meets the tolerance condition
            if self.detected_objects[class_name] >= self.tolerance:
                if class_name not in amount_of_each_class:
                    amount_of_each_class[class_name] = 1
                else:
                    amount_of_each_class[class_name] += 1

    def display_amount_of_each_class(self, frame, amount_of_each_class):
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

    def is_point_inside_rectangle(point, x, y, a, b, c, d):
        """
        Checks if a point is inside a rectangle.

        a,b are the top-left coordinate of the rectangle and (c,d) be its width and height
        """
        if a < x < c and b < y < (b + d):
            return True
        else:
            return False

    def process_video(self):
        if not self.cap.isOpened():
            print("Error: Failed to open the video.")
            exit()

        # draw start and end areas
        area_width = 100
        area_height = 100
        end_area_top_left = (404 - area_width, 900)
        start_area_top_left = (1120, 815)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            cv2.rectangle(
                frame,
                end_area_top_left,
                (end_area_top_left[0] + area_width, end_area_top_left[1] + area_height),
                (0, 0, 255),
                2,
            )
            cv2.rectangle(
                frame,
                start_area_top_left,
                (
                    start_area_top_left[0] + area_width,
                    start_area_top_left[1] + area_height,
                ),
                (0, 0, 255),
                2,
            )

            bboxes, classes, confidences = self.detector.predict(frame)

            # total number of objects detected
            amount_of_each_class = {}
            self.draw_bounding_boxes(
                frame,
                bboxes,
                classes,
                confidences,
                amount_of_each_class,
                (0, 255, 0),
                area_width,
                area_height,
                end_area_top_left,
                start_area_top_left,
            )

            self.display_amount_of_each_class(frame, amount_of_each_class)

            cv2.imshow("frame", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    video_path = "./iceland-traffic-cleaned.mp4"
    model_path = "yolov8m.pt"
    tolerance = 200

    processor = VideoProcessor(video_path, model_path, tolerance)
    processor.process_video()
