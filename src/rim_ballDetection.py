from ultralytics import YOLO
import cv2

# Load the YOLO model
model = YOLO('/Users/matthewxrao/Bench-Buddy/best.pt')

def detect_objects(frame, output_width, output_height):
    # Perform object detection
    results = model(frame)
    ballDetected = False
    rimDetected = False
    shotMadeDetected = False
    
    # Iterate through detected boxes
    for r in results:
        boxes = r.boxes
        
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Extract coordinates
            cls = int(box.cls[0])
            
            # Draw boxes on detected objects (optional)
            color = (255, 0, 0)  # Default color: red
            if cls == 0:  # Ball
                ballDetected = True
                color = (0, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            elif cls == 3:  # Rim
                rimDetected = True
                color = (0, 0, 255)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            elif cls == 1:  # Made Shot
                shotMadeDetected = True
                color = (255, 255, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    
    # Get the original dimensions of the frame
    h, w = frame.shape[:2]
    
    # Calculate the center crop dimensions
    aspect_ratio_output = output_width / output_height
    aspect_ratio_frame = w / h
    
    # Determine cropping dimensions based on aspect ratio
    if aspect_ratio_frame > aspect_ratio_output:
        # Frame is wider than output, crop width
        new_width = int(h * aspect_ratio_output)
        new_height = h
    else:
        # Frame is taller than output, crop height
        new_width = w
        new_height = int(w / aspect_ratio_output)
    
    # Calculate center coordinates for cropping
    x_start = (w - new_width) // 2
    y_start = (h - new_height) // 2
    cropped_frame = frame[y_start:y_start + new_height, x_start:x_start + new_width]
    
    # Resize to match desired output size without changing the aspect ratio
    output_frame = cv2.resize(cropped_frame, (output_width, output_height), interpolation=cv2.INTER_AREA)
    
    return ballDetected, rimDetected, shotMadeDetected, output_frame
