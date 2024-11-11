from ultralytics import YOLO
import numpy as np

# Load the YOLO model
model = YOLO('/Users/matthewxrao/Bench-Buddy/best.pt')

def detect_objects(frame,):
    # Perform object detection
    results = model(frame)
    ballDetected = False
    rimDetected = False
    shotDetected = False
    
    # Iterate through detected boxes
    for r in results:
        boxes = r.boxes
        

        for box in boxes:
            cls = int(box.cls[0])
            if cls == 0:  # 0 is class for 'ball'
                ballDetected = True
            elif cls == 3:  # 3 is class for 'rim'
                rimDetected = True
            elif cls == 1:  # 1 is class for "made shot"
                shotDetected = True 
    return ballDetected, rimDetected, shotDetected
