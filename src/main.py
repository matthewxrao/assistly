from cmu_graphics import *
from loadAudios import getCrowdNoise
from objectDetection import detectObjects
import cv2
import threading
import time
import queue 
import visualEffects
from pyfonts import *

#|************************| INITIALIZE APP |************************|#

def onAppStart(app):
    app.width = 650
    app.height = 450
    
    # Initialize camera feed dimensions and positions
    app.camFeedGap = 5
    app.camFeedOutlineLeft = 50
    app.camFeedOutlineTop = 115
    app.camFeedOutlineWidth = app.width - 2 * app.camFeedOutlineLeft
    app.camFeedOutlineHeight = 275
    
    # Calculate actual camera feed dimensions based on outline and gap
    app.camFeedLeft = app.camFeedOutlineLeft + app.camFeedGap
    app.camFeedTop = app.camFeedOutlineTop + app.camFeedGap
    app.camFeedWidth = app.camFeedOutlineWidth - 2 * app.camFeedGap
    app.camFeedHeight = app.camFeedOutlineHeight - 2 * app.camFeedGap
    
    # Initialize shot tracking statistics and streaks
    app.totalShots = 0
    app.madeShots = 0
    app.shotPercentage = 0
    app.currentStreak = 0
    app.bestStreak = 0
    
    app.message = "Click to begin"
    app.shotMade = False
    app.ballStatus = False
    app.rimStatus = False
    app.steps = 0
    app.frameImage = None
    app.crowd = 'people'
    app.crowdSound = Sound(getCrowdNoise(app.crowd))
    app.background = rgb(23, 23, 23)
    app.setMaxShapeCount(10000)

    app.frameQueue = queue.Queue()
    app.ballDetectionPersistenceThreshold = 40
    app.rimDetectionPersistenceThreshold = 20
    app.shotMadePersistenceThreshold = 15  # Increased threshold

    app.ballDetectionCounter = app.ballDetectionPersistenceThreshold  
    app.rimDetectionCounter = app.rimDetectionPersistenceThreshold
    app.shotMadeDetectionCounter = app.shotMadePersistenceThreshold

    # Initialize buttons dictionary with screen-specific button coordinates
    spacing = 10
    buttonWidth = (app.camFeedOutlineWidth - 2 * spacing) // 3
    startX = app.camFeedOutlineLeft
    
    app.buttons = {
        'continue': {
            'left': app.width//2 - 65,
            'top': (app.height//2 + 90),
            'right': app.width//2 + 65,
            'bottom': (app.height//2 + 110),
            'opacity': 100
        },
        'liveView': {
            'left': startX,
            'top': 50,
            'right': startX + buttonWidth,
            'bottom': 80,
            'opacity': 100
        },
        'statistics': {
            'left': startX + buttonWidth + spacing,
            'top': 50,
            'right': startX + 2*buttonWidth + spacing,
            'bottom': 80,
            'opacity': 100
        },
        'sounds': {
            'left': startX + 2*buttonWidth + 2*spacing,
            'top': 50,
            'right': startX + 3*buttonWidth + 2*spacing,
            'bottom': 80,
            'opacity': 100
        }
    }
    
    app.currentTab = 'liveView'
    visualEffects.init_fissure(app)

#|************************| APP FUNCTIONS |************************|#
def drawTabButtons(app):
    for name, coords in app.buttons.items():
        if name == "continue":
            continue
        buttonFill = 'gray' if name == app.currentTab else 'white'
        textFill = 'white' if name == app.currentTab else app.background
        drawRect(coords['left'], coords['top'], 
                coords['right'] - coords['left'], 
                coords['bottom'] - coords['top'], 
                fill=buttonFill, border='gray')
        drawLabel(name.title(), 
                (coords['left'] + coords['right'])/2,
                (coords['top'] + coords['bottom'])/2,
                size=12, font='montserrat', 
                fill=textFill)
        
def drawAssets(app):
    left = (app.width - 75) // 2
    visualEffects.draw_fissure(app)
    drawImage("images/LittleLogo.png", left, -10)


def tabPress(app, x, y):
    for name, coords in app.buttons.items():
        if name == "continue":
            continue
        if (coords['left'] <= x <= coords['right'] and 
            coords['top'] <= y <= coords['bottom']):
            if name != app.currentTab:
                app.currentTab = name
                setActiveScreen(name)

def takeStep(app):
    if not app.frameQueue.empty():
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
            if app.shotMadeDetectionCounter > app.shotMadePersistenceThreshold:
                app.shotMadeDetectionCounter = 0
                app.madeShots += 1
                app.totalShots += 1
                updateShotPercentage(app)
                updateStreak(app, True)
                triggerEffects(app)
        else:
            app.shotMadeDetectionCounter += 1

        app.ballStatus = app.ballDetectionCounter < app.ballDetectionPersistenceThreshold
        app.rimStatus = app.rimDetectionCounter < app.rimDetectionPersistenceThreshold
        app.shotMade = app.shotMadeDetectionCounter < app.shotMadePersistenceThreshold

        app.frameImage = convert_frame_to_url(frame_with_detections)   
        step(app)
        visualEffects.update_fissure(app, time.time())

def step(app):
    app.steps += 1
    if app.steps % 30 == 0:
        app.crowdSound = Sound(getCrowdNoise(app.crowd))
#|************************| START SCREEN |************************|#

def start_onMousePress(app, x, y):
    setActiveScreen('tip')

def start_redrawAll(app):
    centerX, centerY = app.width // 2, app.height // 2
    left, top = (app.width - 350) // 2, (app.height - 350) // 2

    drawImage("images/logo.png", left, top)
    drawLabel(app.message, centerX, centerY + 75, size=25, font='app.geo', fill='white', bold=True)

#|************************| TIP SCREEN |************************|#


def tip_onScreenActivate(app):
    app.message = "I UNDERSTAND IT NOW"

def tip_onMousePress(app, x, y):
    continueButton = app.buttons['continue']
    if (continueButton['left'] <= x <= continueButton['right'] and 
        continueButton['top'] <= y <= continueButton['bottom']):
        startCaptureThread(app)
        setActiveScreen('liveView')

def tip_onMouseMove(app, x, y):
    continueButton = app.buttons['continue']
    if (continueButton['left'] <= x <= continueButton['right'] and 
        continueButton['top'] <= y <= continueButton['bottom']):
        continueButton['opacity'] = 80
    else:
        continueButton['opacity'] = 100


# Starts MVC safe threading for live feed capture
def startCaptureThread(app):
    capture_thread = threading.Thread(target=getFrames, args=(app,))
    capture_thread.daemon = True 
    capture_thread.start()

# Frame by frame live feed capture with object detection
def getFrames(app):
    video = 'tests/test1.mp4'
    cam = cv2.VideoCapture(video) 

    if not cam.isOpened():
        print("Error: Could not open video.")
        return

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        frameX, frameY = app.camFeedWidth, app.camFeedHeight

        ballDetected, rimDetected, shotMadeDetected, frame_with_detections = detectObjects(frame, frameX, frameY)
        app.frameQueue.put((ballDetected, rimDetected, shotMadeDetected, frame_with_detections))
        
    cam.release()
        

def tip_redrawAll(app):
    centerX, y = app.width // 2, (app.height // 2) + 100
    drawAssets(app)
    drawLabel("TIP", 10, 10, size=15, font='app.geo', fill='white', bold=True)
    drawContinueButton(app, centerX, y)
    

def drawContinueButton(app, x, y):
    continueButton = app.buttons['continue']
    drawRect(continueButton['left'], continueButton['top'], 
            continueButton['right'] - continueButton['left'], 
            continueButton['bottom'] - continueButton['top'], 
            fill="white",
            opacity=continueButton['opacity'])
    drawLabel(app.message, x, y, size=10, font='montserrat', 
             fill=app.background, bold=True, align="center")

#|************************| LIVEVIEW SCREEN |************************|#

def liveView_onScreenActivate(app):
    app.currentTab = 'liveView'
    app.message = 'NO CAMERA INPUT'

def liveView_onKeyPress(app, key):
    if key == 'm': 
        simulateShotMade(app)
    elif key == 's':  # Record a missed shot
        app.totalShots += 1
        app.currentStreak = 0  # Reset streak on missed shot
        updateShotPercentage(app)

def liveView_onMousePress(app, x, y):
    tabPress(app, x, y)

# Update shooting percentage based on makes/total
def updateShotPercentage(app):
    if app.totalShots > 0:
        app.shotPercentage = (app.madeShots / app.totalShots) * 100
    else:
        app.shotPercentage = 0

# Update consecutive makes streak
def updateStreak(app, made):
    if made:
        app.currentStreak += 1
        if app.currentStreak > app.bestStreak:
            app.bestStreak = app.currentStreak
    else:
        app.currentStreak = 0

# Converts frame to image URL displayable through CMU Graphics
def convert_frame_to_url(frame):
    temp_path = "tempFrame.jpg"
    cv2.imwrite(temp_path, frame)
    return temp_path

def liveView_onStep(app):
    takeStep(app)

def triggerEffects(app):
    current_time = time.time()
    visualEffects.trigger_fissure(app, current_time)
    app.crowdSound.play(restart=False, loop=False)

def simulateShotMade(app):
    app.shotMade = True
    app.madeShots += 1
    app.totalShots += 1
    updateShotPercentage(app)
    updateStreak(app, True)
    triggerEffects(app)

def liveView_redrawAll(app):
    drawAssets(app)
    drawTabButtons(app)
    drawCameraFeed(app)
    drawShotStats(app)

# Draw shot statistics and streak counters at the bottom of the screen
def drawShotStats(app):
    # Draw basic shot statistics
    statsY = app.height - 20
    drawLabel(f"Total Shots: {app.totalShots}", 
             app.camFeedOutlineLeft + 5, statsY, 
             size=12, font="Noto Sans", align="left", fill='white')
    
    drawLabel(f"Made Shots: {app.madeShots}", 
             app.width//2, statsY, 
             size=12, font="orbitron", align="center", fill='white')
    
    drawLabel(f"Shot %: {app.shotPercentage:.1f}%", 
             app.camFeedOutlineLeft + app.camFeedOutlineWidth - 5, statsY, 
             size=12, font="orbitron", align="right", fill='white')
    
    # Draw streak information
    streakY = statsY - 25
    streakColor = 'orange' if app.currentStreak >= 3 else 'white'  # Highlight hot streaks
    
    drawLabel(f"Current Streak: {app.currentStreak}", 
             app.width//4, streakY, 
             size=12, font="orbitron", align="center", fill=streakColor)
    
    drawLabel(f"Best Streak: {app.bestStreak}", 
             3*app.width//4, streakY, 
             size=12, font="orbitron", align="center", fill='white')

# Draw camera feed with status indicators
def drawCameraFeed(app):
    statusRadius = 5
    ballStatusX, statusY = app.camFeedOutlineLeft + app.camFeedOutlineWidth - 5 , app.camFeedOutlineTop - 10

    ballStatusText = "BALL DETECTED" if app.ballStatus else "BALL NOT DETECTED"
    ballStatusColor = rgb(144, 238, 144) if app.ballStatus else 'orange'

    outlineColor = gradient('gray','lightgray', app.background) if app.rimStatus else gradient('gray','black', app.background)
    rimStatusText = "RIM DETECTED" if app.rimStatus or app.shotMade else "RIM NOT DETECTED"
    centerX = app.camFeedOutlineLeft + app.camFeedOutlineWidth // 2
    centerY = app.camFeedOutlineTop + app.camFeedOutlineHeight // 2

    if app.shotMade:
        outlineColor = gradient('lightSlateGray','white', 'lightskyblue', app.background)

    drawCircle(ballStatusX, statusY, statusRadius, fill=ballStatusColor)
    drawLabel(ballStatusText, ballStatusX - 12, statusY, font="orbitron", size=10, align="right", fill='white')
    
    drawRect(app.camFeedOutlineLeft, app.camFeedOutlineTop, app.camFeedOutlineWidth, app.camFeedOutlineHeight, fill=outlineColor)
    drawLabel(rimStatusText, app.camFeedOutlineLeft + 5, statusY, size=10, font="orbitron", align="left", fill='white')

    if app.frameImage is not None:
        drawImage(app.frameImage, app.camFeedLeft, app.camFeedTop)
    else:
        drawRect(app.camFeedLeft, app.camFeedTop, app.camFeedWidth, app.camFeedHeight, fill=app.background)
        drawLabel(app.message, centerX, centerY, size=12, fill='white')
    
#|************************| STATISTICS SCREEN |************************|#

def statistics_onScreenActivate(app):
    app.currentTab = 'statistics'

def statistics_onStep(app):
    takeStep(app)

def statistics_onMousePress(app, x, y):
    tabPress(app, x, y)

def statistics_redrawAll(app):
    drawAssets(app)
    drawTabButtons(app)

#|************************| SOUNDS SCREEN |************************|#

def sounds_onScreenActivate(app):
    app.currentTab = 'sounds'

def statistics_onStep(app):
    takeStep(app)

def sounds_onMousePress(app, x, y):
    tabPress(app, x, y)

def sounds_redrawAll(app):
    drawAssets(app)
    drawTabButtons(app)

def main():
    runAppWithScreens(initialScreen='start')
 
if __name__ == "__main__":  
    main()