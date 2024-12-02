# objectdetection.py

from ultralytics import YOLO
import cv2
import numpy as np
from c import v
from ekf import ExtendedKalmanFilter

# Initialize YOLO model
model = YOLO('v11.pt')
detClasses = {0: 'Ball', 1: 'Made Shot', 2: 'Person', 3: 'Rim', 4: 'Shot'}

def detectObjects(frame, outputWidth, outputHeight, ekf):
    # Image output resizing
    h, w = frame.shape[:2]

    aspectRatioOutput = outputWidth / outputHeight
    aspectRatioFrame = w / h

    if aspectRatioFrame > aspectRatioOutput:
        newWidth = int(h * aspectRatioOutput)
        newHeight = h
    else:
        newWidth = w
        newHeight = int(w / aspectRatioOutput)

    xStart = (w - newWidth) // 2
    yStart = (h - newHeight) // 2
    croppedFrame = frame[yStart:yStart + newHeight, xStart:xStart + newWidth]

    outputFrame = cv2.resize(croppedFrame, (outputWidth, outputHeight), interpolation=cv2.INTER_AREA)

    results = model(outputFrame, conf=0.6, batch=10, device='mps')
    ballDetected = False
    rimDetected = False
    shotMadeDetected = False
    p = 0

    # Variables to store ball measurements
    ball_measurements = []

    for r in results:
        boxes = r.boxes

        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])

            if cls == 2 or cls == 4:  # Skip detection for "Person" and "Shot" class
                continue

            color = None
            if cls == 0:  # Ball
                ballDetected = True 
                center_x = int((x1 + x2) / 2)
                center_y = int((y1 + y2) / 2)
                radius = int(abs(x2 - x1) / 2)
                p = v(outputFrame, (center_x, center_y), radius)
                ball_measurements.append(np.array([center_x, center_y]))
            elif cls == 3:  # Rim
                rimDetected = True
                color = (0, 0, 255)
            elif cls == 1:  # Made Shot
                shotMadeDetected = True
                color = (255, 250, 205)

            if color:
                cv2.rectangle(outputFrame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(outputFrame, detClasses[cls].upper(), (x1, y1 - 10),
                            cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 2)

    # Prediction Step
    ekf.predict()

    if ball_measurements:
        # If multiple ball detections, choose the one with the highest confidence or closest to previous position
        z = ball_measurements[0]
        ekf.update(z)
    else:
        # If no detection rely on prediction
        pass

    # Get current state estimate
    state = ekf.get_state()
    est_x, est_y, __, ___ = state

    cv2.circle(frame, (int(est_x), int(est_y)), p, (255, 255, 255), p)

    return ballDetected, rimDetected, shotMadeDetected, outputFrame
