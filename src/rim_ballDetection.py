from ultralytics import YOLO
import numpy as np

# Load a pre-trained YOLOv8 model once at the start
model = YOLO('yolov8n.pt')  # or use a custom-trained model

def detect_objects(frame):
    results = model(frame)
    
    ball_bbox = None
    rim_bbox = None
    
    for r in results:
        boxes = r.boxes
        for box in boxes:
            cls = int(box.cls[0])
            if cls == 32:  # COCO class for sports ball
                ball_bbox = box.xyxy[0].cpu().numpy().astype(int)
            elif cls == 36:  # COCO class for baseball glove (approximated for basketball rim)
                rim_bbox = box.xyxy[0].cpu().numpy().astype(int)
    
    return ball_bbox, rim_bbox
