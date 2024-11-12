from cmu_graphics import *
import cv2
import threading
from rim_ballDetection import detect_objects
import queue

def onAppStart(app):
    app.height = 1920
    app.width = 1080
    app.message = "Press Space to Start"
    app.shotMade = False
    app.ballStatus = False
    app.rimStatus = False
    app.steps = 0
    app.frame_image = None 
    import pathlib
    local_path = "/Users/matthewxrao/Bench-Buddy/audios/people2.mp3"
    file_url = pathlib.Path(local_path).as_uri()
    app.sound = Sound(file_url)

def start_onKeyPress(app, key):
    if key == 'space':
        setActiveScreen('capture')

def start_redrawAll(app):
    centerX, centerY = app.width // 2, app.height // 2
    drawLabel(app.message, centerX, centerY, size=25, font="orbitron")

def capture_onScreenActivate(app):
    startCaptureThread(app)
    app.message = 'NO CAMERA INPUT'

def capture_onStep(app):
    if not data_queue.empty():
        # Get the latest data from the queue
        ballDetected, rimDetected, shotMadeDetected, frame_with_detections = data_queue.get()
        
        # Update the app state with the new data
        app.ballStatus = ballDetected
        app.rimStatus = rimDetected
        app.shotMade = shotMadeDetected
        app.frame_image = convert_frame_to_url(frame_with_detections)   
    step(app)

def step(app):
    app.steps += 1

def startCaptureThread(app):
    # Create a new thread to handle video capture
    capture_thread = threading.Thread(target=capture, args=(app,))
    capture_thread.daemon = True  # Ensures the thread ends when the app closes
    capture_thread.start()

# Open qeaue for data
data_queue = queue.Queue()

def capture(app):
    video = 'tests/test1.mp4' # Test Purposes Only
    # Initialize video capture
    cam = cv2.VideoCapture(video) 
    
    if not cam.isOpened():
        print("Error: Could not open video.")
        return

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        frameX, frameY = app.width - 100, app.height - 100
        # Detect objects in the frame
        ballDetected, rimDetected, shotMadeDetected, frame_with_detections = detect_objects(frame, frameX, frameY)
        
        # Update status in a thread-safe way
        data_queue.put((ballDetected, rimDetected, shotMadeDetected, frame_with_detections))
        
    cam.release()

def convert_frame_to_url(frame):
    # Save the frame to a temporary file and return the path
    temp_path = "temp_detected_frame.jpg"
    cv2.imwrite(temp_path, frame)
    return temp_path

def capture_redrawAll(app):
    drawBallStatus(app)
    drawRimStatus(app)

    centerX, centerY = app.width // 2, app.height // 2

    if app.shotMade:
        drawRect(centerX - 150, centerY - 50, 300, 100, fill='red')
        drawLabel("Shot Made", centerX, centerY, size=40, fill='white', align='center')
        app.sound.play(restart=False, loop=False)

def drawBallStatus(app):
    statusRadius = 8
    gap = 20
    ballStatusX, ballStatusY = app.width - 40, 15

    ballStatusMessage = "BALL DETECTED" if app.ballStatus else "BALL NOT DETECTED"
    ballStatusColor = 'green' if app.ballStatus else 'red'
    drawCircle(ballStatusX, ballStatusY, statusRadius, fill=ballStatusColor)
    drawLabel(ballStatusMessage, ballStatusX - gap, ballStatusY, font="orbitron", size=20, align="right")


def drawRimStatus(app):
    gap = 20
    centerX, centerY = app.width // 2, app.height // 2
    rimBoxX, rimBoxY = 30, 30
    rimBoxWidth, rimBoxHeight = app.width - 60, app.height - 60
    rimFillX, rimFillY = rimBoxX + gap, rimBoxY + gap
    rimFillWidth, rimFillHeight = rimBoxWidth - 2 * gap, rimBoxHeight - 2 * gap
    rimStatusColor = 'green' if app.rimStatus else 'red'
    rimStatusText = "RIM DETECTED" if app.rimStatus or app.shotMade else "RIM NOT DETECTED"

    drawRect(rimBoxX, rimBoxY, rimBoxWidth, rimBoxHeight,  fill = rimStatusColor)
    if app.frame_image is not None:
        # Display the frame image detected with bounding boxes
        drawImage(app.frame_image, rimFillX, rimFillY)
    else:
        drawRect(rimFillX, rimFillY, rimFillWidth, rimFillHeight,  fill = "white")
        drawLabel(app.message, centerX, centerY, size=25)
    drawLabel(rimStatusText, rimBoxX, rimBoxY - 15, size=20, font="orbitron",align="left")

def main():
    runAppWithScreens(initialScreen='start')

if __name__ == "__main__":
    main()
