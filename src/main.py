from cmu_graphics import *
from loadAudios import getCrowdNoise
from objectDetection import detectObjects
import cv2
import threading
import queue

def onAppStart(app):
    app.width = 680
    app.height = 420
    app.message = "Press Space to Start"
    app.shotMade = False
    app.ballStatus = False
    app.rimStatus = False
    app.steps = 0
    app.frameImage = None
    app.crowd = 'people'
    app.crowdSound = Sound(getCrowdNoise(app.crowd))
    app.background = 'black'

    # Initialize queue for MVC-safe frame updating
    app.frameQueue = queue.Queue()
    
    # Frame threshold for stickier rim and ball detection
    app.ballDetectionPersistenceThreshold = 40
    app.rimDetectionPersistenceThreshold = 20
    app.shotMadePersistenceThreshold = 10

    # Initialize counters for ball and rim detection beginning at threshold
    app.ballDetectionCounter = app.ballDetectionPersistenceThreshold  
    app.rimDetectionCounter = app.rimDetectionPersistenceThreshold
    app.shotMadeDetectionCounter = app.shotMadePersistenceThreshold
    

def start_onKeyPress(app, key):
    if key == 'space':
        setActiveScreen('capture')

def start_redrawAll(app):
    centerX, centerY = app.width // 2, app.height // 2
    drawLabel(app.message, centerX, centerY, size=25, font='montserrat', fill='white', bold=True)

def capture_onScreenActivate(app):
    startCaptureThread(app)
    app.message = 'NO CAMERA INPUT'

def capture_onStep(app):
    if not app.frameQueue.empty():
        # Get the latest data from the queue
        ballDetected, rimDetected, shotMadeDetected, frame_with_detections = app.frameQueue.get()

        if ballDetected:
            app.ballDetectionCounter = 0
        else:
            app.ballDetectionCounter += 1
        if rimDetected:
            app.rimDetectionCounter = 0
        else:
            app.rimDetectionCounter += 1
        if shotMadeDetected:
            app.shotMadeDetectionCounter = 0
        else:
            app.shotMadeDetectionCounter += 1

        # Only update when persistence threshold is met
        app.ballStatus = app.ballDetectionCounter < app.ballDetectionPersistenceThreshold
        app.rimStatus = app.rimDetectionCounter < app.rimDetectionPersistenceThreshold
        app.shotMade = app.shotMadeDetectionCounter < app.shotMadePersistenceThreshold

        app.frameImage = convert_frame_to_url(frame_with_detections)   
        step(app)

def step(app):
    app.steps += 1
    if app.steps % 100 == 0:
        app.crowdSound = Sound(getCrowdNoise(app.crowd))

def startCaptureThread(app):
    capture_thread = threading.Thread(target=getFrames, args=(app,))
    capture_thread.daemon = True 
    capture_thread.start()



def getFrames(app):
    video = 'tests/test2.mp4' # Test Purposes Only

    # Initialize video capture
    cam = cv2.VideoCapture(0) 
    
    if not cam.isOpened():
        print("Error: Could not open video.")
        return

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        frameX, frameY = app.width - 160, app.height - 110
        # Detect objects in the frame
        ballDetected, rimDetected, shotMadeDetected, frame_with_detections = detectObjects(frame, frameX, frameY)
        
        # Update status in a thread-safe way
        app.frameQueue.put((ballDetected, rimDetected, shotMadeDetected, frame_with_detections))
        
    cam.release()

# Function to convert cv2 frame to create temp image URL displayable in cmu_graphics
def convert_frame_to_url(frame):
    temp_path = "tempFrame.jpg"
    cv2.imwrite(temp_path, frame)
    return temp_path

def capture_redrawAll(app):
    drawFeed(app)

    centerX, centerY = app.width // 2, app.height // 2

    
def drawFeed(app):
    # Ball Status
    statusRadius = 5
    ballStatusX, ballStatusY = app.width - 140, 15

    ballStatusText = "BALL DETECTED" if app.ballStatus else "BALL NOT DETECTED"
    ballStatusColor = rgb(144, 238, 144) if app.ballStatus else 'orange'

    # Rim Status
    outlineLeft, outlineTop = 20, 25
    outlineWidth, outlineHeight = app.width - 150, app.height - 100
    outlineColor = gradient( 'lightSlateGray','white', 'lightskyblue', 'black') if app.rimStatus else gradient( 'gray','lightgray', 'black')
    rimStatusText = "RIM DETECTED" if app.rimStatus or app.shotMade else "RIM NOT DETECTED"
    centerX, centerY = outlineLeft + outlineWidth // 2, outlineTop + outlineHeight // 2 

    # Overide Outline Color if Shot Made
    if app.shotMade:
        app.crowdSound.play(restart=False, loop=False)
        outlineColor = gradient( 'lightSlateGray','white', 'lemonChiffon', 'black')

    # Camera Feed
    gap = 5
    camFeedLeft, camFeedTop = outlineLeft + gap, outlineTop + gap
    camFeedWidth, camFeedHeight = outlineWidth - 2 * gap, outlineHeight - 2 * gap


    # Draw the ball status
    drawCircle(ballStatusX, ballStatusY, statusRadius, fill=ballStatusColor)
    drawLabel(ballStatusText, ballStatusX - 12, ballStatusY, font="orbitron", size=12, align="right", fill='white')
    
    # Draw the outline
    drawRect(outlineLeft, outlineTop, outlineWidth, outlineHeight,  fill = outlineColor)
    drawLabel(rimStatusText, outlineLeft + 5, 15, size=12, font="orbitron",align="left", fill='white')

    # Draw the camera feed
    if app.frameImage is not None:
        drawImage(app.frameImage, camFeedLeft, camFeedTop)
    else:
        drawRect(camFeedLeft, camFeedTop, camFeedWidth, camFeedHeight,  fill = app.background)
        drawLabel(app.message, centerX, centerY, size=20, fill='white')

def main():
    runAppWithScreens(initialScreen='start')

if __name__ == "__main__":
    main()