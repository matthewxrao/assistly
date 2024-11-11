from cmu_graphics import *
import cv2
import threading
from rim_ballDetection import detect_objects


#********************************************************* #
# ************************ MODEL ************************* #
#********************************************************* #

def onAppStart(app):
    app.height = 1920
    app.width = 1080
    app.message = "Press Space to Start"
    app.shotMade = False
    app.ballStatus = False
    app.rimStatus = False
    app.steps = 0

#********************************************************* #
# ******************** START SCREEN ********************** #
#********************************************************* #

def start_onKeyPress(app, key):
    if key == 'space':
        setActiveScreen('capture')

def start_redrawAll(app):
    centerX, centerY = app.width/2, app.height/2
    drawLabel(app.message, centerX, centerY, size=25)

#*********************************************************** #
# ******************** CAPTURE SCREEN ********************** #
#*********************************************************** #

def capture_onStep(app):
    # Updates redrawAll to express change of variables in thread
    app.steps += 1

def capture_onScreenActivate(app):
    app.message = "IDEK"
    startCaptureThread(app)

def capture_redrawAll(app):
    centerX, centerY = app.width/2, app.height/2
    gap = 15
    statusRadius = 5
    ballStatusX = app.width - 20
    ballStatusY = app.width - 70


    drawLabel(app.message, centerX, centerY, size=25)
    
    # Ball Status
    ballStatusColor = 'green' if app.ballStatus else 'red'
    drawCircle(ballStatusX, 20, statusRadius, fill=ballStatusColor)
    drawLabel("Ball", ballStatusX - statusRadius - gap, 20, size=10)
    
    # Rim Status
    rimStatusColor = 'green' if app.rimStatus else 'red'
    drawCircle(ballStatusY, 20, statusRadius, fill=rimStatusColor)
    drawLabel("Rim", ballStatusY - statusRadius - gap, 20, size=10)

    # Updates "Shot Made" message
    if app.shotMade:
        drawRect(centerX, centerY, 50, 50, fill='red')
        drawLabel("Shot Made", 125, 435, size=50)


def startCaptureThread(app):
    # Create a new thread to handle video capture
    capture_thread = threading.Thread(target=capture, args=(app,))
    capture_thread.daemon = True  # This ensures the thread ends when the app closes
    capture_thread.start()


def capture(app):
    # Initialize video capture
    cam = cv2.VideoCapture('/Users/matthewxrao/Bench-Buddy/tests/Youth Basketball Drills 2v2 Advantage.mp4')
    
    if not cam.isOpened():
        print("Error: Could not open video.")
        return

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        ballDetected, rimDetected, shotMadeDetected = detect_objects(frame)
        
        app.ballStatus = True if ballDetected else False
        app.rimStatus = True if rimDetected else False
        app.shotMade = True if shotMadeDetected else False

    cam.release()

def main():
    runAppWithScreens(initialScreen='start')


if __name__ == "__main__":
    main()
