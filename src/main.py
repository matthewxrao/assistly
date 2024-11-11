import cv2
from rim_ballDetection import detect_objects
from shotAnalysis import check_shot

def main():
    # Initialize video capture
    cam = cv2.VideoCapture('/Users/matthewxrao/Bench-Buddy/tests/Basketball Shooting Drill Short Long.mp4')

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        ball_bbox, rim_bbox = detect_objects(frame)
        
        # Draw bounding boxes
        if ball_bbox is not None:
            cv2.rectangle(frame, (ball_bbox[0], ball_bbox[1]), 
                         (ball_bbox[2], ball_bbox[3]), (0, 255, 0), 2)
        if rim_bbox is not None:
            cv2.rectangle(frame, (rim_bbox[0], rim_bbox[1]), 
                         (rim_bbox[2], rim_bbox[3]), (255, 0, 0), 2)
        
        # Update shot analysis
        check_shot(ball_bbox, rim_bbox)
        
        cv2.imshow('Basketball Tracking', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
