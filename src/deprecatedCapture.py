import cv2
from rim_ballDetection import detect_objects

def deprecatedCapture():
    # Initialize video capture
    cam = cv2.VideoCapture('/Users/matthewxrao/Bench-Buddy/tests/Youth Basketball Drills 2v2 Advantage.mp4')
    
    if not cam.isOpened():
        print("Error: Could not open video.")
        return

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        # Get bounding boxes and shot made status from object detection
        ballStatus, rimStatus, shotMade = detect_objects(frame)
        
        # Draw bounding boxes if detected
        if ballStatus is not None:
            cv2.rectangle(frame, (ballStatus[0], ballStatus[1]), 
                         (ballStatus[2], ballStatus[3]), (0, 255, 0), 2)  # Green box for ball
        if rimStatus is not None:
            cv2.rectangle(frame, (rimStatus[0], rimStatus[1]), 
                         (rimStatus[2], rimStatus[3]), (0, 0, 255), 2)  # Blue box for rim
        
        # Display "Made Shot" message if the shot is detected
        if shotMade:
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, 'Made Shot!', (300, 300), font, 1, (0, 0, 255), 2, cv2.LINE_AA)

        # Display the frame with bounding boxes and message
        cv2.imshow('Basketball Tracking', frame)
        
        # Break the loop if the user presses 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()