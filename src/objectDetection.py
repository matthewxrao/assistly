from ultralytics import YOLO
import cv2

model = YOLO('/Users/matthewxrao/Bench-Buddy/v11.pt')
detClasses = {0: 'Ball', 1: 'Made Shot', 2: 'Person', 3: 'Rim', 4: 'Shot'}

def detectObjects(frame, outputWidth, outputHeight):
    results = model(frame, conf=0.6, batch=10, device='mps')
    ballDetected = False
    rimDetected = False
    shotMadeDetected = False

    for r in results:
        boxes = r.boxes
        
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls = int(box.cls[0])
            
            color = None
            if cls == 0:  # Ball
                ballDetected = True 
                cv2.circle(frame, (int((x1 + x2) / 2), int((y1 + y2) / 2)), int(abs(x2 - x1)) // 2,(255, 255, 255), 2)
            elif cls == 3: # Rim
                rimDetected = True
                color = (0, 0, 255)
            elif cls == 1: # ShotMade
                shotMadeDetected = True
                color = (255, 250, 205)
            
            if color:
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, detClasses[cls].upper(), (x1, y1 - 10), cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 2)
    
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
    
    return ballDetected, rimDetected, shotMadeDetected, outputFrame