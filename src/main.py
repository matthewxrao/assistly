import pathlib
from cmu_graphics import *
from loadAudios import getCrowdNoise
from objectDetection import detectObjects
from ekf import ExtendedKalmanFilter
import cv2
import random
import threading
import time
import queue 
import visualEffects
from PIL import ImageGrab 

#|************************| APP CONFIG & INITIALIZATION |************************|#

def onAppStart(app):
    """
    Initializes the application state, including dimensions, stats, sounds, UI elements,
    data structures, and starting values for detection counters.
    """
    # App dimensions
    app.width = 650
    app.height = 460
    app.background = rgb(23, 23, 23)
    app.setMaxShapeCount(10000)
    
    # Camera feed layout configuration
    app.camFeedGap = 5
    app.camFeedOutlineLeft = 50
    app.camFeedOutlineTop = 115
    app.camFeedOutlineWidth = app.width - 2 * app.camFeedOutlineLeft
    app.camFeedOutlineHeight = 275
    
    # Actual camera feed dimensions (inside outline)
    app.camFeedLeft = app.camFeedOutlineLeft + app.camFeedGap
    app.camFeedTop = app.camFeedOutlineTop + app.camFeedGap
    app.camFeedWidth = app.camFeedOutlineWidth - 2 * app.camFeedGap
    app.camFeedHeight = app.camFeedOutlineHeight - 2 * app.camFeedGap

    # Initialize shot stats and streaks
    app.totalShots = 0
    app.madeShots = 0
    app.shotPercentage = 0
    app.currentStreak = 0
    app.bestStreak = 0

    # Detection states and messages
    app.message = "Click to begin"
    app.shotMade = False
    app.ballStatus = False
    app.rimStatus = False
    app.steps = 0
    app.frameImage = None

    # Sound and crowd initialization
    app.crowd = 'humans'
    app.crowdSound = Sound(getCrowdNoise(app.crowd))

    # Initialize special effects
    visualEffects.init_fissure(app)

    # Queues & thresholds for detection persistence
    app.frameQueue = queue.Queue()
    app.ballDetectionPersistenceThreshold = 40
    app.rimDetectionPersistenceThreshold = 20
    app.shotMadePersistenceThreshold = 20

    app.ballDetectionCounter = app.ballDetectionPersistenceThreshold  
    app.rimDetectionCounter = app.rimDetectionPersistenceThreshold
    app.shotMadeDetectionCounter = app.shotMadePersistenceThreshold

    # Stats and graph data
    app.sessionStartTime = 0
    app.shotHistory = []  
    app.graphPoints = []  
    app.graphMargin = 40 
    app.minGraphMinutes = 0.083

    # Graph dimensions
    app.graphLeft = app.camFeedOutlineLeft + 50
    app.graphTop = app.camFeedOutlineTop
    app.graphWidth = app.camFeedOutlineWidth - 225
    app.graphHeight = app.camFeedOutlineHeight
    app.hoveredPoint = None
    app.hoveringGraph= False

    # Session variables
    app.isRunning = False
    app.sessionEndTime = None
    app.sessionHoveredPoint = None

    # Shot history panel
    app.historyLeft = app.camFeedOutlineLeft + (app.camFeedOutlineWidth - 200) + 20
    app.historyTop = app.camFeedOutlineTop + 30
    app.historyWidth = 200
    app.historyHeight = 150
    app.currentTab = 'liveView'

    # Manual mode variables
    app.manualMode = False
    app.hoveredZone = None
    app.showLocationPrompt = False
    app.tempShotLocation = None
    app.zoneSelectionTime = None
    app.locationPromptStartTime = 0
    app.locationPromptDuration = 5 # seconds
    app.lastShotLocation = None

    # Court zones for manual mode annotation

    app.courtZones = {
        '1': {'name': 'left_corner', 'makes': 0, 'attempts': 0},
        '2': {'name': 'left_wing', 'makes': 0, 'attempts': 0},
        '3': {'name': 'left_midrange', 'makes': 0, 'attempts': 0},
        '4': {'name': 'paint', 'makes': 0, 'attempts': 0},
        '5': {'name': 'top_key', 'makes': 0, 'attempts': 0},
        '6': {'name': 'right_midrange', 'makes': 0, 'attempts': 0},
        '7': {'name': 'right_wing', 'makes': 0, 'attempts': 0},
        '8': {'name': 'right_corner', 'makes': 0, 'attempts': 0},
    }

    app.manualModeButton = {
        'left': app.width//2 - 75,
        'top': (app.height//2 + 165),
        'right': app.width//2 - 65,
        'bottom': (app.height//2 + 175),
        'opacity': 100
    }

    # Initialize UI elements for sounds & tabs
    setSoundButtons(app)
    setTabButtons(app)


#|************************| UI LAYOUT & BUTTONS |************************|#

def setTabButtons(app):
    """
    Configures the tab buttons (liveView, stats, sounds) and their layout.
    """
    spacing = 10
    buttonWidth = (app.camFeedOutlineWidth - 2 * spacing) // 3
    startX = app.camFeedOutlineLeft
    
    app.buttons = {
        'continue': {
            'left': app.width//2 - 75,
            'top': (app.height//2 + 120),
            'right': app.width//2 + 75,
            'bottom': (app.height//2 + 150),
            'opacity': 100
        },
        'liveView': {
            'left': startX,
            'top': 50,
            'right': startX + buttonWidth,
            'bottom': 80,
            'opacity': 100
        },
        'stats': {
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

def setSoundButtons(app):
    """
    Configures the sound selection buttons on the 'sounds' tab.
    """
    paddingY = 30
    paddingX = 30
    buttonWidth = (app.camFeedOutlineWidth - 2) // 2 - paddingX//2
    buttonHeight = (app.camFeedOutlineHeight + 20)//2 - paddingY//2
    
    baseLeft = app.camFeedOutlineLeft
    baseTop = app.camFeedOutlineTop
    app.soundButtons = {
        'humans': {
            'left': baseLeft,
            'top': baseTop,
            'right': baseLeft + buttonWidth,
            'bottom': baseTop + buttonHeight,
            'opacity': 60
        },
        'dogs' : {
            'left': baseLeft + buttonWidth + paddingX,
            'top': baseTop,
            'right': baseLeft + 2*buttonWidth + paddingX,
            'bottom': baseTop + buttonHeight,
            'opacity': 60
        },
        'minions' : {
            'left': baseLeft,
            'top': baseTop + buttonHeight + paddingY,
            'right': baseLeft + buttonWidth,
            'bottom': baseTop + 2*buttonHeight + paddingY,
            'opacity': 60
        },
        'cows' : {
            'left': baseLeft + buttonWidth + paddingX,
            'top': baseTop + buttonHeight + paddingY,
            'right': baseLeft + 2*buttonWidth + paddingX,
            'bottom': baseTop + 2*buttonHeight + paddingY,
            'opacity': 60
        }
    }


#|************************| UTILITIES & HELPER FUNCTIONS |************************|#

def convert_frame_to_url(frame):
    """
    Writes a captured frame to disk as a temporary image and returns its path,
    allowing CMU Graphics to display it.
    """
    temp_path = "tempFrame.jpg"
    cv2.imwrite(temp_path, frame)
    return temp_path


def updateShotPercentage(app):
    """
    Recalculate and update the shot percentage based on current makes and attempts.
    """
    if app.totalShots > 0:
        app.shotPercentage = (app.madeShots / app.totalShots) * 100
    else:
        app.shotPercentage = 0


def updateStreak(app, made):
    """
    Update the current streak and best streak counters based on whether a shot was made.
    """
    if made:
        app.currentStreak += 1
        if app.currentStreak > app.bestStreak:
            app.bestStreak = app.currentStreak
    else:
        app.currentStreak = 0


def showShotLocationPrompt(app):
    """
    Prompt the user to enter a shot location when in manual mode.
    """
    app.showLocationPrompt = True
    app.locationPromptStartTime = time.time()


def updateZoneStats(app, zone, made):
    """
    Update zone-level shooting stats when a shot is assigned a zone.
    """
    if zone in app.courtZones:
        app.courtZones[zone]['attempts'] += 1
        if made:
            app.courtZones[zone]['makes'] += 1


#|************************| CORE APP LOGIC & DETECTION |************************|#

def takeStep(app):
    """
    Process the next frame in the queue and update detection states, shots, stats, and effects.
    Called periodically by onStep methods.
    """
    if not app.frameQueue.empty():
        ballDetected, rimDetected, shotMadeDetected, frame_with_detections = app.frameQueue.get()

        # Update ball detection persistence
        app.ballDetectionCounter = 0 if ballDetected else app.ballDetectionCounter + 1
        
        # Update rim detection persistence
        app.rimDetectionCounter = 0 if rimDetected else app.rimDetectionCounter + 1

        # Check if shot made is detected
        if shotMadeDetected:
            # Confirm shot made only if we were previously above persistence threshold
            if app.shotMadeDetectionCounter > app.shotMadePersistenceThreshold:
                app.shotMadeDetectionCounter = 0
                recordShotResult(app, made=True)
        else:
            app.shotMadeDetectionCounter += 1

        # Set boolean states based on counters
        app.ballStatus = app.ballDetectionCounter < app.ballDetectionPersistenceThreshold
        app.rimStatus = app.rimDetectionCounter < app.rimDetectionPersistenceThreshold
        app.shotMade = app.shotMadeDetectionCounter < app.shotMadePersistenceThreshold

        # Update displayed frame
        app.frameImage = convert_frame_to_url(frame_with_detections)
        visualEffects.update_fissure(app, time.time())


def recordShotResult(app, made, timestamp=None):
    """
    Handles all logic when a shot result is finalized (either from detection or simulation).
    This function updates stats, shot history, streaks, triggers effects, and prompts manual 
    mode location selection if applicable.
    """
    # Use current time if no timestamp is provided
    if timestamp is None:
        timestamp = time.time()
    
    # Update counters
    app.totalShots += 1
    if made:
        app.madeShots += 1
        triggerEffects(app)
    
    # Append shot history (zone unknown at this moment, can be updated after prompt)
    app.shotHistory.append((app.totalShots, made, timestamp, None))
    
    # Update stats and streaks
    updateShotPercentage(app)
    updateStreak(app, made)
    updateStats(app)
    app.crowdSound = Sound(getCrowdNoise(app.crowd))

     # If in manual mode, prompt for location
    if app.manualMode:
        showShotLocationPrompt(app)
    
    # Periodic updates (e.g. changing crowd sounds)
    step(app)

def step(app):
    """
    Periodic global updates.
    """
    app.steps += 1


def updateStats(app):
    """
    Update the stats data structure (graphPoints) after each shot, reflecting performance over time.
    """
    currentTime = time.time()
    elapsedMinutes = (currentTime - app.sessionStartTime) / 60

    if app.totalShots > 0:
        percentage = (app.madeShots / app.totalShots) * 100
        # Record or update graph points
        if len(app.graphPoints) == 0:
            app.graphPoints.append((elapsedMinutes, percentage, app.totalShots))
        elif app.totalShots > app.graphPoints[-1][2]:
            app.graphPoints.append((elapsedMinutes, percentage, app.totalShots))
        else:
            lastPoint = app.graphPoints[-1]
            app.graphPoints[-1] = (elapsedMinutes, lastPoint[1], lastPoint[2])


def triggerEffects(app):
    """
    Trigger special effects (crowd cheer, fissure) after a successful shot.
    """
    current_time = time.time()
    visualEffects.trigger_fissure(app, current_time)
    app.crowdSound.play(restart=False, loop=False)


def simulateShotMade(app):
    """
    Manually simulate a made shot.
    """
    recordShotResult(app, made=True)


def simulateShotMissed(app):
    """
    Manually simulate a missed shot.
    """
    recordShotResult(app, made=False)


def startCaptureThread(app):
    """
    Start a separate thread to read frames from the video source and perform object detection.
    """
    app.isRunning = True  
    capture_thread = threading.Thread(target=getFrames, args=(app,))
    capture_thread.daemon = True 
    capture_thread.start()


def getFrames(app):
    """
    Continuously read frames from a video source, perform object detection, and enqueue results.
    """
    video = 'tests/test7.mp4'
    cam = cv2.VideoCapture(0) 

    if not cam.isOpened():
        print("Error: Could not open video.")
        return

    fps = cam.get(cv2.CAP_PROP_FPS)
    ekf = ExtendedKalmanFilter(dt=fps, process_noise_std=1.0, measurement_noise_std=10.0)

    while app.isRunning:
        ret, frame = cam.read()
        if not ret:
            break
        
        frameX, frameY = app.camFeedWidth, app.camFeedHeight
        ballDetected, rimDetected, shotMadeDetected, frame_with_detections = detectObjects(frame, frameX, frameY, ekf)
        app.frameQueue.put((ballDetected, rimDetected, shotMadeDetected, frame_with_detections))
        
    cam.release()


#|************************| COMMON DRAWING FUNCTIONS |************************|#

def drawAssets(app):
    """
    Draw common assets like the fissure effect and the top logo.
    """
    left = (app.width - 35) // 2
    visualEffects.draw_fissure(app)
    drawImage("images/logo.png", left, 10, width=35, height=35)


def drawTabButtons(app):
    """
    Draws the navigation tabs at the top (liveView, stats, sounds).
    """
    for name, coords in app.buttons.items():
        if name == "continue":
            continue
        elif name == "liveView":
            text = "live feed"
        else:
            text = name.title()

        buttonFill = app.background if name == app.currentTab else 'white'
        textFill = 'white' if name == app.currentTab else app.background
        drawRect(coords['left'], coords['top'], 
                 coords['right'] - coords['left'], 
                 coords['bottom'] - coords['top'], 
                 fill=buttonFill, border='white', opacity=coords["opacity"])
        drawLabel(text.upper(), 
                  (coords['left'] + coords['right'])/2,
                  (coords['top'] + coords['bottom'])/2,
                  size=12, bold=True, 
                  fill=textFill)


#|************************| TAB NAVIGATION & EVENT HANDLERS |************************|#

def tabPress(app, x, y):
    """
    Handle mouse presses on the tab buttons to switch screens.
    """
    for name, coords in app.buttons.items():
        if name == "continue":
            continue
        elif (coords['left'] <= x <= coords['right'] and 
              coords['top'] <= y <= coords['bottom']):
            if name != app.currentTab:
                app.currentTab = name
                setActiveScreen(name)


def tabHover(app, x, y):
    """
    Handle hover states for tab buttons, changing their opacity.
    """
    for name, coords in app.buttons.items():
        if name == "continue":
            continue
        if (coords['left'] <= x <= coords['right'] and 
            coords['top'] <= y <= coords['bottom']):
            if name != app.currentTab:
                coords["opacity"] = 80
        else:
            coords["opacity"] = 100


def keypress(app, key):
    """
    Handle global keypress actions for debugging or screen transitions.
    """
    if key == 'm': 
        simulateShotMade(app)
    elif key == 's':
        simulateShotMissed(app)
    elif key == 'f':
        setActiveScreen('session')


#|************************| START SCREEN |************************|#

def start_onMousePress(app, x, y):
    setActiveScreen('tip')

def start_redrawAll(app):
    centerX, centerY = app.width // 2, app.height // 2
    left, top = (app.width - 100) // 2, centerY - 75

    drawImage("images/logo.png", left, top, width=100, height=100)
    drawLabel("ASSISTLY", centerX, top + 100 + 10, size=20, fill='white', bold=True)
    drawLabel(app.message, centerX, centerY + 100, size=12, fill='white', italic=True, bold=True)


#|************************| TIP SCREEN |************************|#

def tip_onScreenActivate(app):
    """
    Called when the 'tip' screen is activated. Sets up continue and manual mode toggle buttons.
    """
    app.message = "I UNDERSTAND IT NOW"

def tip_onMousePress(app, x, y):
    continueButton = app.buttons['continue']
    if (continueButton['left'] <= x <= continueButton['right'] and 
        continueButton['top'] <= y <= continueButton['bottom']):
        app.sessionStartTime = time.time()
        startCaptureThread(app)
        setActiveScreen('liveView')

def tip_onKeyPress(app, key):
    if key == 't':
        app.manualMode = not app.manualMode

def tip_onMouseMove(app, x, y):
    continueButton = app.buttons['continue']
    button = app.manualModeButton
    if (continueButton['left'] <= x <= continueButton['right'] and 
        continueButton['top'] <= y <= continueButton['bottom']):
        continueButton['opacity'] = 80
    elif (button['left'] <= x <= button['right'] and
          button['top'] <= y <= button['bottom']):
        button['opacity'] = 80
    else:
        continueButton['opacity'] = 100
        button['opacity'] = 100

def drawManualModeButton(app):
    """
    Draw the toggle button to enable/disable manual mode on the tip screen.
    """
    button = app.manualModeButton
    message = "MANUAL MODE" if app.manualMode else "AUTO MODE"
    drawLabel(message,
              app.width//2,
              (button['top'] + button['bottom'])/2,
              size=10, fill='white', align='center', bold=True)

def drawContinueButton(app, x):
    """
    Draw the continue button on the tip screen.
    """
    continueButton = app.buttons['continue']
    drawRect(continueButton['left'], continueButton['top'], 
             continueButton['right'] - continueButton['left'], 
             continueButton['bottom'] - continueButton['top'], 
             fill="white",
             opacity=continueButton['opacity'])
    height = continueButton['bottom'] - continueButton['top']
    drawLabel(app.message, x, continueButton['top'] + height//2, size=10, fill=app.background, bold=True, align="center")

def tip_redrawAll(app):
    centerX, y = app.width // 2, (app.height // 2) + 65
    drawAssets(app)
    drawLabel("TIP", centerX, 65, size=15, fill='white', bold=True)
    drawImage("images/tip.png", centerX - 125, 75, width=250, height=250)
    drawLabel("For best detection results ensure the camera is at an angle", centerX, y, size=12, bold=True, align='center', fill='white')
    drawLabel("between 30 - 45 degrees to the basket", centerX, y + 15, size=12, bold=True, align='center', fill='white')
    drawLabel("*** Press T to Toggle Mode ***", centerX, y + 40, size=12, bold=True, align='center', fill='white')
    drawContinueButton(app, centerX)
    drawManualModeButton(app)


#|************************| LIVEVIEW SCREEN |************************|#

def liveView_onScreenActivate(app):
    """
    Initialize the liveView screen when activated.
    """
    app.currentTab = 'liveView'
    app.message = 'NO CAMERA INPUT'

def liveView_onKeyPress(app, key):
    """
    If location prompt is active and user presses a number, assign that zone.
    """
    if app.showLocationPrompt and key in '12345678':
        zone = key
        app.tempShotLocation = zone
        app.zoneSelectionTime = time.time()  # Record the time of selection
        if app.shotHistory:
            shotNum, made, timestamp, _ = app.shotHistory[-1]
            app.shotHistory[-1] = (shotNum, made, timestamp, zone)
        updateZoneStats(app, zone, made)
        return
    else:
        keypress(app, key)

def liveView_onMousePress(app, x, y):
    tabPress(app, x, y)

def liveView_onMouseMove(app, x, y):
    tabHover(app, x, y)

def liveView_onStep(app):
    """
    Periodic update while on the liveView screen. Handles time-bound location prompts.
    """
    takeStep(app)

    if app.showLocationPrompt:
        timeElapsed = time.time() - app.locationPromptStartTime
        if timeElapsed > app.locationPromptDuration:
            app.showLocationPrompt = False
            if app.shotHistory:
                shotNum, made, timestamp, _ = app.shotHistory[-1]
                app.shotHistory[-1] = (shotNum, made, timestamp, None)
                updateZoneStats(app, None, made)
    
    if app.zoneSelectionTime is not None:
        if (time.time() - app.zoneSelectionTime) > 0.2:
            app.tempShotLocation = None
            app.zoneSelectionTime = None
            app.showLocationPrompt = False
        
def liveView_redrawAll(app):
    drawAssets(app)
    drawTabButtons(app)
    drawCameraFeed(app)
    drawShotStats(app)
    if app.showLocationPrompt: 
        drawShotLocationPrompt(app)


#|************************| LIVEVIEW DRAWING FUNCTIONS |************************|#

def drawCurrentStreak(app):
    """
    Draws the current streak icon on the liveView screen.
    """
    x = app.camFeedOutlineLeft + 378
    y = app.height - 77
    if app.currentStreak < 3:
        drawImage("images/nostreak.png", x, y, width=64, height=64, opacity=100)
    else:
        hotstreak_files = list(pathlib.Path('images/hotstreak').glob('*.png'))
        hotstreak_path = random.choice(hotstreak_files)
        drawImage(str(hotstreak_path), x+2, y - 5, width=60, height=60, opacity=100)

def drawBestStreak(app):
    """
    Draws the best streak icon on the liveView screen.
    """
    drawImage("images/beststreak.png", app.camFeedOutlineLeft + 485, app.height - 75, width=60, height=60, opacity=100)

def drawShotStats(app):
    """
    Draws the shot stats and streak counters at the bottom of the liveView screen.
    """
    statsY = app.height - 45
    # Made Shots
    drawLabel(f"{app.madeShots}", 
              app.camFeedOutlineLeft + 20, statsY + 2, 
              size=35, bold=True, align="center", fill='white')
    drawLabel("MADE", app.camFeedOutlineLeft + 20, statsY + 30, size=8, bold=True, fill='white')

    # Attempts
    drawLabel(f"{app.totalShots}", 
              app.camFeedOutlineLeft + 110, statsY + 2, 
              size=35, bold=True, align="center", fill='white')
    drawLabel("ATTEMPTS", app.camFeedOutlineLeft + 110, statsY + 30, size=8, bold=True, fill='white')

    # FG Percentage
    drawLabel(f"{app.shotPercentage:.1f}%", 
              app.camFeedOutlineLeft + 210, statsY + 2, 
              size=35, bold=True, align="center", fill='white')
    drawLabel("FG PERCENTAGE", app.camFeedOutlineLeft + 210, statsY + 30, size=8, bold=True, fill='white')
    
    # Current Streak
    currentStreakText = 'fireBrick' if app.currentStreak >= 3 else 'black'
    drawCurrentStreak(app)
    drawLabel(f"{app.currentStreak}", 
              app.camFeedOutlineLeft + 410, statsY, 
              size=30, bold=True, align="center", fill=currentStreakText)
    drawLabel("CURRENT STREAK", app.camFeedOutlineLeft + 410, statsY + 30, size=8, bold=True, fill='white')
    
    # Best Streak
    drawBestStreak(app)
    drawLabel(f"{app.bestStreak}", 
              app.camFeedOutlineLeft + 515, statsY, 
              size=30, bold=True, align="center", fill='darkslateblue')
    drawLabel("BEST STREAK", app.camFeedOutlineLeft + 515, statsY + 30, size=8, bold=True, fill='white')

def drawCameraFeed(app):
    """
    Draws the camera feed area and status indicators (ball/rim detection).
    """
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

    # Ball Status
    drawCircle(ballStatusX, statusY, statusRadius, fill=ballStatusColor)
    drawLabel(ballStatusText, ballStatusX - 12, statusY, bold=True, size=10, align="right", fill='white')
    
    # Rim Outline & Text
    drawRect(app.camFeedOutlineLeft, app.camFeedOutlineTop, app.camFeedOutlineWidth, app.camFeedOutlineHeight, fill=outlineColor)
    drawLabel(rimStatusText, app.camFeedOutlineLeft + 5, statusY, size=10, bold=True, align="left", fill='white')

    # Draw Frame or Placeholder
    if app.frameImage is not None:
        drawImage(app.frameImage, app.camFeedLeft, app.camFeedTop)
    else:
        drawRect(app.camFeedLeft, app.camFeedTop, app.camFeedWidth, app.camFeedHeight, fill=app.background)
        drawLabel(app.message, centerX, centerY, size=12, bold=True, fill='white')

def drawShotLocationPrompt(app):
    """
    Displays the shot location prompt overlay and, if a zone was selected recently,
    flashes the selected zone image for up to one second.
    """
    if not app.showLocationPrompt:
        return
    
    zoneSelectedRecently = False
    if app.tempShotLocation and app.zoneSelectionTime is not None:
        zoneSelectedRecently = True

    # Draw overlay and images
    drawRect(0, 0, app.width, app.height, fill='black', opacity=90)

    imageLeft = app.width//2 - 200
    imageTop = app.height//2 - 150
    imageWidth = 400
    imageHeight = 300

    if zoneSelectedRecently:
        # Show the selected zone image
        drawImage(f"images/heatmap/{app.tempShotLocation}/0.png", imageLeft, imageTop, width=imageWidth, height=imageHeight)
    else:
        # Show empty heatmap image if still within prompt duration (or for the flashing effect after prompt closed)
        drawImage("images/heatmap/empty.png", imageLeft, imageTop, width=imageWidth, height=imageHeight)

    timeElapsed = time.time() - app.locationPromptStartTime
    timeLeft = max(0, app.locationPromptDuration - timeElapsed)
    
    labelY = imageTop - 30
    drawLabel(f"Select shot location ({timeLeft:.1f}s)",
                app.width//2, labelY,
                fill='white', bold=True, size=20)

    drawLabel("Press corresponding number on keyboard to assign location",
                app.width//2,
                labelY + 20,
                fill='white',
                bold=True,
                size=14)

    # Countdown bar
    barWidth = 400
    barHeight = 20
    barLeft = app.width//2 - barWidth//2
    barTop = imageTop + imageHeight + 20
    progress = timeLeft / app.locationPromptDuration

    drawRect(barLeft, barTop, barWidth, barHeight, fill='white', opacity=30)
    fillWidth = barWidth * progress if progress > 0 else 0.1
    drawRect(barLeft, barTop, fillWidth, barHeight, fill='white', opacity=80)

#|************************| STATS SCREEN |************************|#

def stats_onScreenActivate(app):
    app.currentTab = 'stats'

def stats_onStep(app):
    takeStep(app)

def stats_onKeyPress(app, key):
    keypress(app,key)

def stats_onMousePress(app, x, y):
    tabPress(app, x, y)

def stats_onMouseMove(app, x, y):
    """
    Handle mouse movement on the stats screen, for hovering over data points in the graph.
    """
    tabHover(app, x, y)
    currentTime = time.time()
    elapsedMinutes = (currentTime - app.sessionStartTime) / 60
    timeWindow = max(elapsedMinutes, app.minGraphMinutes)
    
    if (app.graphLeft <= x <= app.graphLeft + app.graphWidth and
            app.graphTop <= y <= app.graphTop + app.graphHeight):
        app.hoveringGraph = True
    else:
        app.hoveringGraph = False

    app.hoveredPoint = None
    for i, point in enumerate(app.graphPoints):
        pointX = app.graphLeft + (point[0] / timeWindow) * app.graphWidth
        pointY = app.graphTop + app.graphHeight - (point[1]/100 * app.graphHeight)
        
        # Check if mouse is near a graph point
        if ((x - pointX)**2 + (y - pointY)**2) <= 100:
            app.hoveredPoint = i
            break


#|************************| STATS SCREEN DRAWING |************************|#

def formatTimeLabel(minutes):
    """
    Formats a time value in minutes into a human-readable string with minutes/seconds.
    """
    totalSeconds = int(minutes * 60)
    mins = totalSeconds // 60
    secs = totalSeconds % 60
    if mins == 0:
        return f"{secs}s"
    elif secs == 0:
        return f"{mins}m"
    else:
        return f"{mins}m {secs}s"

def formatTimeHeader(minutes):
    """
    Formats a time value in minutes into MM:SS format for display.
    """
    totalSeconds = int(minutes * 60)
    mins = totalSeconds // 60
    secs = totalSeconds % 60
    if secs < 10:
        secs = f"0{secs}"
    if mins < 10:
        mins = f"0{mins}"
    return f"{mins}:{secs}"

def drawInfoBox(app, x, y, pointIndex, percentage, made, total):
    """
    Draws an information box near a hovered data point in the graph, showing shot stats.
    """
    if app.manualMode:
        boxWidth = 150
        boxHeight = 180
        padding = 10
    else:
        boxWidth = 85
        boxHeight = 95 
        padding = 10

    graphTop = app.graphTop
    graphHeight = app.graphHeight

    boxTop = y - boxHeight - padding
    if boxTop < graphTop:
        boxTop = y + padding
    
    boxLeft = x - boxWidth/2

    # Extract shot info
    if pointIndex <= len(app.shotHistory):
        _, make, timestamp, location = app.shotHistory[pointIndex - 1]
        timestamp = formatTimeHeader((timestamp - app.sessionStartTime) / 60)
    else:
        make = None
        timestamp = formatTimeHeader(0)
    
    outlineColor = 'limegreen' if make else ('crimson' if make is not None else 'white')
    
    drawRect(boxLeft, boxTop, boxWidth, boxHeight, 
             fill=app.background, opacity=90, border=outlineColor)

    textY = boxTop + 12
    spacing = 15
    
    drawLabel(f"SHOT {total}", boxLeft + boxWidth/2, textY, fill='white', size=12, bold=True)
    textY += spacing
    drawLabel(f"MADE: {made}", boxLeft + boxWidth/2, textY, fill='white', size=9)
    textY += spacing
    drawLabel(f"MISSED: {total - made}", boxLeft + boxWidth/2, textY, fill='white', size=9)
    textY += spacing
    drawLabel(f"FG %: {percentage:.1f}%", boxLeft + boxWidth/2, textY, fill='white', size=9)
    textY += spacing
    drawLabel(f"{timestamp}", boxLeft + boxWidth/2, textY, fill='white', size=9, bold=True)
    textY += 5
    imageHeight = boxHeight - (textY - boxTop + 12 )
    if app.manualMode:
        if not location:
            drawLabel("NO LOGGED LOCATION", boxLeft + boxWidth/2, textY + imageHeight // 2, fill='white', size=9, bold=True)
        else:
            drawImage(f"images/heatmap/{location}/0.png", boxLeft + padding, textY, width=boxWidth - 2 * padding, height=imageHeight)

def drawPoint(app, x, y, isHovered, isCurrent=False):
    """
    Draw a point on the stats graph, highlighting it if hovered.
    """
    baseRadius = 5
    if isHovered:
        drawCircle(x+1, y+1, baseRadius+2, fill='gray', opacity=40)
        drawCircle(x, y, baseRadius+2, fill='white')
    else:
        drawCircle(x, y, baseRadius, fill='white')

def drawGraph(app):
    """
    Draws the performance graph (FG% over time) on the stats screen.
    """
    currentTime = time.time()
    elapsedMinutes = (currentTime - app.sessionStartTime) / 60
    timeWindow = max(elapsedMinutes, app.minGraphMinutes)
    
    drawRect(app.graphLeft, app.graphTop, app.graphWidth, app.graphHeight, 
             fill=None, border='white')
    
    # Time markers
    numTimeMarkers = 5
    for i in range(numTimeMarkers + 1):
        timeValue = (timeWindow * i) / numTimeMarkers
        x = app.graphLeft + (i * app.graphWidth / numTimeMarkers)
        timeLabel = formatTimeLabel(timeValue)
        drawLabel(timeLabel, x, app.graphTop + app.graphHeight + 20,
                  fill='white', bold=True, size=10)
        if i > 0:
            drawLine(x, app.graphTop, x, app.graphTop + app.graphHeight,
                     fill='gray', opacity=30)
    
    drawLabel("TIME", 
              app.graphLeft + app.graphWidth/2, 
              app.graphTop + app.graphHeight + 35,
              fill='white', bold=True, size=12)
    drawLabel("FG %", 
              app.graphLeft - 45, 
              app.graphTop + app.graphHeight/2,
              fill='white', bold=True, size=12, rotateAngle=270)
    
    # FG% markers
    for i in range(0, 101, 20):
        y = app.graphTop + app.graphHeight - (i/100 * app.graphHeight)
        drawLabel(f"{i}%", app.graphLeft - 10, y, 
                  fill='white', bold=True, size=10, align='right')
        drawLine(app.graphLeft, y, app.graphLeft + app.graphWidth, y,
                 fill='gray', opacity=30)
    
    # Draw data lines
    if len(app.graphPoints) > 0:
        x0 = app.graphLeft
        # First point
        x1 = app.graphLeft + (app.graphPoints[0][0] / timeWindow) * app.graphWidth
        y1 = app.graphTop + app.graphHeight - (app.graphPoints[0][1]/100 * app.graphHeight)
        drawLine(x0, y1, x1, y1, fill='lightBlue', lineWidth=2)
        drawPoint(app, x1, y1, app.hoveredPoint == 0)
        
        fx, fy, fi = 0, 0, 0
        # Middle points
        for i in range(len(app.graphPoints)-1):
            x1 = app.graphLeft + (app.graphPoints[i][0] / timeWindow) * app.graphWidth
            y1 = app.graphTop + app.graphHeight - (app.graphPoints[i][1]/100 * app.graphHeight)
            x2 = app.graphLeft + (app.graphPoints[i+1][0] / timeWindow) * app.graphWidth
            y2 = app.graphTop + app.graphHeight - (app.graphPoints[i+1][1]/100 * app.graphHeight)
            
            drawLine(x1, y1, x2, y2, fill='lightBlue', lineWidth=2)
            drawPoint(app, x1, y1, app.hoveredPoint == i)
            
            if app.hoveredPoint == i:
                fx, fy, fi = x1, y1, i
        
        # Last point
        lastX = app.graphLeft + (app.graphPoints[-1][0] / timeWindow) * app.graphWidth
        lastY = app.graphTop + app.graphHeight - (app.graphPoints[-1][1]/100 * app.graphHeight)
        currentX = app.graphLeft + (elapsedMinutes / timeWindow) * app.graphWidth
        
        drawLine(lastX, lastY, currentX, lastY, fill='lightBlue', lineWidth=2)
        isLastPointHovered = app.hoveredPoint == len(app.graphPoints)-1
        drawPoint(app, lastX, lastY, isLastPointHovered)
        
        # Info box for hovered points
        if not app.hoveringGraph and app.hoveredPoint is None:
            drawInfoBox(app, lastX, lastY, len(app.graphPoints), 
                        app.shotPercentage, app.madeShots, app.totalShots)
        if app.hoveredPoint is not None and not isLastPointHovered:
            madeShots = int((app.graphPoints[fi][1] / 100) * app.graphPoints[fi][2])
            drawInfoBox(app, fx, fy, fi+1, app.graphPoints[fi][1], 
                        madeShots, app.graphPoints[fi][2])
        elif isLastPointHovered:
            drawInfoBox(app, lastX, lastY, len(app.graphPoints),
                        app.shotPercentage, app.madeShots, app.totalShots)

def drawShotHistory(app):
    """
    Draws a panel on the stats screen showing recent shot history and elapsed session time.
    """
    currentTime = time.time()
    elapsedMinutes = (currentTime - app.sessionStartTime) / 60

    drawLabel("TIME ELAPSED",
              app.historyLeft + app.historyWidth/2,
              app.historyTop - 25,
              bold=True,
              fill='white', size=10)
    timeLabel = formatTimeHeader(elapsedMinutes)
    drawLabel(f"{timeLabel}",
              app.historyLeft + app.historyWidth/2,
              app.historyTop,
              bold=True,
              fill='white', size=40)
    
    shotHeight = 18
    shotWidth = app.historyWidth - 40
    startY = app.historyTop + 54

    lastShots = app.shotHistory[-10:] if len(app.shotHistory) > 0 else []
    lastShots.reverse()
    # Drawing last 10 shots in reverse order
    for i, (_, wasMade, timestamp, __) in enumerate(lastShots):
        y = startY + (i * (shotHeight + 1))
        shotColor = "limegreen" if wasMade else 'crimson'
        shotText = "MAKE" if wasMade else "MISS"
        shotTime = formatTimeHeader((timestamp - app.sessionStartTime) / 60)
        
        drawRect(app.historyLeft + 20, y, 
                 shotWidth, shotHeight,
                 fill=shotColor, opacity=90)
        
        drawLabel(shotText, 
                  app.historyLeft + 20 + shotWidth/2, y + shotHeight/2,
                  fill='white', size=10, bold=True, align='center')
        drawLabel(f"{shotTime}", app.historyLeft + 25, y + shotHeight/2,
                  fill='white', size=10, align='left', bold=True)
    
    drawRect(app.historyLeft + 20, startY - 20, shotWidth, app.camFeedOutlineHeight - 55 - startY, fill='white')
    drawLabel("SHOT HISTORY",
              app.historyLeft + app.historyWidth/2,
              app.historyTop + 45,
              bold=True,
              fill=app.background, size=12)
    drawRect(app.historyLeft + 20, startY - 20, shotWidth, app.camFeedOutlineHeight - 64, fill=None, border='white')

def stats_redrawAll(app):
    drawAssets(app)
    drawTabButtons(app)
    drawShotHistory(app)
    drawGraph(app)


#|************************| SOUNDS SCREEN |************************|#

def sounds_onScreenActivate(app):
    app.currentTab = 'sounds'

def drawSoundButtons(app):
    """
    Draws the four sound option buttons (humans, dogs, minions, cows).
    """
    for name, coords in app.soundButtons.items():
        textFill = 'white'
        outline = 'white' if name == app.crowd else 'gray'
        drawRect(coords['left'], coords['top'], 
                 coords['right'] - coords['left'], 
                 coords['bottom'] - coords['top'], 
                 fill=app.background, border=outline, borderWidth=5, opacity=coords["opacity"])
        drawLabel(name.upper(), 
                  (coords['left'] + coords['right'])/2,
                  (coords['top'] + coords['bottom'])/2,
                  size=12, bold=True, 
                  fill=textFill)

def soundButtonHover(app, x, y):
    """
    Adjust opacity of sound buttons on hover.
    """
    for name, coord in app.soundButtons.items():
        if (coord['left'] <= x <= coord['right'] and 
            coord['top'] <= y <= coord['bottom']) and name != app.crowd:
            coord['opacity'] = 100
        elif name == app.crowd:
            coord['opacity'] = 100
        else:
            coord['opacity'] = 60

def soundButtonPress(app, x, y):
    """
    Change the crowd sound based on user's button press.
    """
    for name, coord in app.soundButtons.items():
        if (coord['left'] <= x <= coord['right'] and 
            coord['top'] <= y <= coord['bottom']):
            app.crowd = name
            app.crowdSound = Sound(getCrowdNoise(app.crowd))

def sound_onKeyPress(app, key):
    keypress(app,key)

def sounds_onStep(app):
    takeStep(app)

def sounds_onMouseMove(app, x, y):
    tabHover(app, x, y)
    soundButtonHover(app, x, y)

def sounds_onMousePress(app, x, y):
    tabPress(app, x, y)
    soundButtonPress(app, x, y)

def sounds_redrawAll(app):
    drawAssets(app)
    drawTabButtons(app)
    drawSoundButtons(app)


#|************************| SESSION (END) SCREEN |************************|#

def session_onScreenActivate(app):
    """
    Called when the session ends. Stop the capture thread, clear queues, finalize stats,
    and identify hot/cold streak periods for summary.
    """
    app.currentTab = 'session'
    app.message = "SESSION SUMMARY"
    
    app.isRunning = False  
    app.frameQueue = queue.Queue()
    app.frameImage = None
    app.crowdSound = None
    
    app.sessionEndTime = time.time()
    app.hotPeriod, app.coldPeriod = findStreakPeriods(app)
    app.sessionHoveredPoint = None

    app.exportButton = {
        'left': app.width - 150,
        'top': 20,
        'right': app.width - 20,
        'bottom': 50,
        'opacity': 100
    }

def session_onMousePress(app, x, y):
    """
    Handle mouse presses on the session screen, including the export button.
    """
    if (app.exportButton['left'] <= x <= app.exportButton['right'] and 
        app.exportButton['top'] <= y <= app.exportButton['bottom']):
        app.exportButton["opacity"] = 0
        exportSessionSummary(app)


def session_onMouseMove(app, x, y):
    """
    Handle mouse movement on the session screen, including hovering over the export button.
    """
    
    if (app.exportButton['left'] <= x <= app.exportButton['right'] and 
        app.exportButton['top'] <= y <= app.exportButton['bottom']):
        app.exportButton['opacity'] = 80
    else:
        app.exportButton['opacity'] = 100
    

    if app.manualMode:
        graphLeft = 50
        graphTop = 140
        graphWidth = app.width//2 - 75
        graphHeight = 200
    else:
        graphLeft = 60
        graphTop = 140
        graphWidth = app.width - 100
        graphHeight = 200
    
    # Check if mouse is within graph bounds
    if (graphLeft <= x <= graphLeft + graphWidth and 
        graphTop <= y <= graphTop + graphHeight):
        
        # Find nearest point
        app.sessionHoveredPoint = None
        if len(app.graphPoints) > 0:
            for i, point in enumerate(app.graphPoints):
                pointX = graphLeft + (point[0] / app.graphPoints[-1][0]) * graphWidth
                pointY = graphTop + graphHeight - (point[1] / 100) * graphHeight
                
                if ((x - pointX)**2 + (y - pointY)**2) <= 100:  # 10px radius
                    app.sessionHoveredPoint = i
                    break
    else:
        app.sessionHoveredPoint = None

def drawExportButton(app):
    """
    Draws the export button on the session screen.
    """
    drawRect(app.exportButton['left'], app.exportButton['top'], 
             app.exportButton['right'] - app.exportButton['left'], 
             app.exportButton['bottom'] - app.exportButton['top'], 
             fill='white', opacity=app.exportButton['opacity'])
    drawLabel("EXPORT", 
              (app.exportButton['left'] + app.exportButton['right']) / 2,
              (app.exportButton['top'] + app.exportButton['bottom']) / 2,
              size=10, bold=True, fill=app.background, align='center')

def drawExportButton(app):
    """
    Draws the export button on the session screen.
    """
    drawRect(app.exportButton['left'], app.exportButton['top'], 
             app.exportButton['right'] - app.exportButton['left'], 
             app.exportButton['bottom'] - app.exportButton['top'], 
             fill='white', opacity=app.exportButton['opacity'])
    drawLabel("EXPORT", 
              (app.exportButton['left'] + app.exportButton['right']) / 2,
              (app.exportButton['top'] + app.exportButton['bottom']) / 2,
              size=10, bold=True, fill=app.background, align='center')

def session_redrawAll(app):
    centerX = app.width // 2
    drawAssets(app)
    drawLabel(app.message, centerX, 60, size=20, bold=True, fill='white')
    drawOverallStats(app, centerX)
    drawHotColdPeriods(app)
    drawExportButton(app)
    if app.manualMode:
        drawCourtHeatmap(app)
    drawShootingTrendsGraph(app)

def exportSessionSummary(app):
    """
    Exports the session summary as a screenshot.
    """

    screenshot = ImageGrab.grab()
    screenshot.save("session_summary.png") 
    print("Session summary exported as session_summary.png")

#|************************| SESSION SUMMARY ANALYSIS |************************|#

def findStreakPeriods(app):
    """
    Analyze the shot history to find the hottest and coldest streak periods of shooting.
    A "hot" period is one with at least 3 makes in a window, and a "cold" period is one
    with at least 3 misses. Also considers consecutive streaks.
    """
    if len(app.shotHistory) < 3:
        return None, None

    window_size = 5
    best_hot_period = None
    best_cold_period = None
    max_hot_percentage = 0
    min_cold_percentage = 100
    
    current_streak = []
    longest_make_streak = []
    longest_miss_streak = []
    
    # Analyze shots for rolling windows and longest streaks
    for i, shot in enumerate(app.shotHistory):
        shot_num, made, timestamp, location = shot
        
        # Consecutive streak tracking
        if not current_streak or current_streak[0][1] == made:
            current_streak.append(shot)
        else:
            if current_streak[0][1]:
                if len(current_streak) > len(longest_make_streak):
                    longest_make_streak = current_streak.copy()
            else:
                if len(current_streak) > len(longest_miss_streak):
                    longest_miss_streak = current_streak.copy()
            current_streak = [shot]
        
        # Rolling window analysis
        if i >= window_size - 1:
            window = app.shotHistory[i-window_size+1:i+1]
            makes_in_window = sum(1 for _, m, _, _ in window if m)
            percentage = (makes_in_window / window_size) * 100
            
            # Update hot period
            if percentage > max_hot_percentage and makes_in_window >= 3:
                max_hot_percentage = percentage
                best_hot_period = (
                    window[0][2],
                    window[-1][2],
                    percentage,
                    window_size,
                    True,
                    [shot[0] for shot in window]
                )
            
            # Update cold period
            if percentage < min_cold_percentage and (window_size - makes_in_window) >= 3:
                min_cold_percentage = percentage
                best_cold_period = (
                    window[0][2],
                    window[-1][2],
                    percentage,
                    window_size,
                    False,
                    [shot[0] for shot in window]
                )
    
    # Check final streak
    if current_streak:
        if current_streak[0][1]:
            if len(current_streak) > len(longest_make_streak):
                longest_make_streak = current_streak
        else:
            if len(current_streak) > len(longest_miss_streak):
                longest_miss_streak = current_streak

    hot_period = None
    cold_period = None
    
    # Determine final hot period
    if longest_make_streak and len(longest_make_streak) >= 3:
        consecutive_hot = (
            longest_make_streak[0][2],
            longest_make_streak[-1][2],
            100.0,
            len(longest_make_streak),
            True,
            [shot[0] for shot in longest_make_streak]
        )
        hot_period = consecutive_hot if not best_hot_period else \
            max([consecutive_hot, best_hot_period], key=lambda x: (x[2], x[3]))
    else:
        hot_period = best_hot_period
    
    # Determine final cold period
    if longest_miss_streak and len(longest_miss_streak) >= 3:
        consecutive_cold = (
            longest_miss_streak[0][2],
            longest_miss_streak[-1][2],
            0.0,
            len(longest_miss_streak),
            False,
            [shot[0] for shot in longest_miss_streak]
        )
        cold_period = consecutive_cold if not best_cold_period else \
            min([consecutive_cold, best_cold_period], key=lambda x: (x[2], -x[3]))
    else:
        cold_period = best_cold_period

    return hot_period, cold_period

def drawHotColdPeriods(app):
    """
    Draws overlays/text on the session summary showing the identified hot and cold streak periods.
    """
    if app.hotPeriod or app.coldPeriod:
        hotY = 380
        
        # Hot period box
        if app.hotPeriod:
            hotLeft = 50
            drawRect(hotLeft, hotY, 250, 60, fill=None, border='orange')
            drawLabel(f"HOTTEST STREAK ({app.hotPeriod[3]} CONSECUTIVE MAKES)", 
                      hotLeft + 125, hotY + 15, 
                      size=10, bold=True, fill='orange')
            timeStart = formatTimeHeader((app.hotPeriod[0] - app.sessionStartTime) / 60)
            timeEnd = formatTimeHeader((app.hotPeriod[1] - app.sessionStartTime) / 60)
            drawLabel(f"{timeStart} - {timeEnd}", 
                      hotLeft + 125, hotY + 35, size=12, fill='white')
        
        # Cold period box
        if app.coldPeriod:
            coldLeft = app.width - 300
            drawRect(coldLeft, hotY, 250, 60, fill=None, border='lightBlue')
            drawLabel(f"COLDEST STREAK ({app.coldPeriod[3]} CONSECUTIVE MISSES)", 
                      coldLeft + 125, hotY + 15,
                      size=10, bold=True, fill='lightBlue')
            timeStart = formatTimeHeader((app.coldPeriod[0] - app.sessionStartTime) / 60)
            timeEnd = formatTimeHeader((app.coldPeriod[1] - app.sessionStartTime) / 60)
            drawLabel(f"{timeStart} - {timeEnd}",
                      coldLeft + 125, hotY + 35, size=12, fill='white')

def drawOverallStats(app, centerX): 
    """
    Draws overall session stats (duration, FG%, shots/min) on the end session screen.
    """
    sessionDuration = (app.sessionEndTime - app.sessionStartTime) / 60
    shotsPerMinute = app.totalShots / sessionDuration if sessionDuration > 0 else 0
    
    statsY = 87
    mins = int(sessionDuration)
    secs = int((sessionDuration - mins) * 60)
    timeStr = f"{mins:02d}:{secs:02d}"
    
    drawLabel("SESSION DURATION", centerX - 200, statsY, size=12, bold=True, fill='white')
    drawLabel(timeStr, centerX - 200, statsY + 25, size=24, bold=True, fill='white')
    
    drawLabel("FG %", centerX, statsY, size=12, bold=True, fill='white')
    drawLabel(f"{app.shotPercentage:.1f}%", centerX, statsY + 25, size=24, bold=True, fill='white')
    
    drawLabel("SHOTS/MIN", centerX + 200, statsY, size=12, bold=True, fill='white')
    drawLabel(f"{shotsPerMinute:.1f}", centerX + 200, statsY + 25, size=24, bold=True, fill='white')

def drawShootingTrendsGraph(app):
    """
    Draw the shooting trends graph (FG% over time) on the end session screen.
    If manual mode is enabled, graph dimensions are smaller (half screen).
    """
    if app.manualMode:
        graphLeft = 50
        graphTop = 140
        graphWidth = app.width//2 - 75
        graphHeight = 200
    else:
        graphLeft = 60
        graphTop = 140
        graphWidth = app.width - 100
        graphHeight = 200
    
    drawRect(graphLeft, graphTop, graphWidth, graphHeight, 
             fill=None, border='white')
    
    if len(app.graphPoints) > 0:
        totalTime = app.graphPoints[-1][0]
        
        # Time labels
        for i in range(6):
            timeVal = totalTime * i / 5
            x = graphLeft + (timeVal / totalTime) * graphWidth
            timeLabel = formatTimeLabel(timeVal)
            drawLabel(timeLabel, x, graphTop + graphHeight + 20,
                      fill='white', bold=True, size=10)
    
        # FG% labels
        for i in range(0, 101, 20):
            y = graphTop + graphHeight - (i/100 * graphHeight)
            drawLabel(f"{i}%", graphLeft - 10, y,
                      fill='white', bold=True, size=10, align='right')
        
        # Highlight hot/cold periods
        if app.hotPeriod:
            hotStartMin = (app.hotPeriod[0] - app.sessionStartTime) / 60
            hotEndMin = (app.hotPeriod[1] - app.sessionStartTime) / 60
            hotStart = graphLeft + (hotStartMin / totalTime) * graphWidth
            hotEnd = min(graphLeft + (hotEndMin / totalTime) * graphWidth, graphLeft + graphWidth)  
            drawRect(hotStart, graphTop, hotEnd - hotStart, graphHeight,
                     fill='orange', opacity=20)

        if app.coldPeriod:
            coldStartMin = (app.coldPeriod[0] - app.sessionStartTime) / 60
            coldEndMin = (app.coldPeriod[1] - app.sessionStartTime) / 60
            coldStart = graphLeft + (coldStartMin / totalTime) * graphWidth
            coldEnd = min(graphLeft + (coldEndMin / totalTime) * graphWidth, graphLeft + graphWidth) 
            drawRect(coldStart, graphTop, coldEnd - coldStart, graphHeight,
                     fill='lightblue', opacity=20)
        
        # Draw trend line and points
        prevX = None
        prevY = None
        fx, fy, fi = 0, 0, 0
        hovered = False

        for i, point in enumerate(app.graphPoints):
            x = graphLeft + (point[0] / totalTime) * graphWidth
            y = graphTop + graphHeight - (point[1] / 100) * graphHeight
            
            if prevX is not None:
                drawLine(prevX, prevY, x, y, fill='lightBlue', lineWidth=2)
            
            isHovered = (app.sessionHoveredPoint == i)
            pointRadius = 5 if isHovered else 3
            drawCircle(x, y, pointRadius, fill='white')
            
            if isHovered:
                fx, fy, fi = x, y, i
                hovered = True
            
            prevX = x
            prevY = y
            
        if hovered:
            drawInfoBox(app, fx, fy, fi+1, app.graphPoints[fi][1], 
                        int(app.graphPoints[fi][1] * app.graphPoints[fi][2] / 100), 
                        int(app.graphPoints[fi][2]))

def drawCourtHeatmap(app):
    """
    Draw a simple court representation and a zone-based heatmap. Each zone's shooting percentage is mapped 
    into quartiles and the corresponding image is displayed.
    """
    if not app.manualMode:
        return

    courtLeft = app.width // 2 + 25
    courtTop = 140
    courtWidth = app.width // 2 - 75
    courtHeight = 200


    for zone_key, stats in app.courtZones.items():
        attempts = stats['attempts']
        makes = stats['makes']

        if attempts < 3:
            continue
        else:
            percentage = (makes / attempts) * 100

            if percentage < 20:
                quartile = 1
            elif percentage < 40:
                quartile = 2
            elif percentage < 60:
                quartile = 3
            else:
                quartile = 4
            drawImage(f"images/heatmap/{zone_key}/{quartile}.png", courtLeft, courtTop, width=courtWidth, height=courtHeight)
    
    padding = 60
    boxTop = courtTop + courtHeight + 10
    colors = [rgb(13, 73, 204), rgb(71, 129, 255), rgb(255, 89, 89), rgb(206, 0, 0)]
    for i in range(1, 5):
        percentage = f"{20*(i-1)}% - {20*i}%" if i < 4 else f"{60}% - {100}%"
        boxLeft = courtLeft + padding * (i - 1)

        drawRect(boxLeft, boxTop, 6, 6, fill=colors[i-1])
        drawLabel(percentage, boxLeft + 10, boxTop + 3, fill='white', align="left", bold=True, size=9)
    drawLabel("MIN. 3 SHOT ATTEMPTS", courtLeft + courtWidth//2, boxTop + 16, fill='white', align="center", bold=True, italic=True ,size=9)

        

#|************************| MAIN ENTRY |************************|#

def main():
    runAppWithScreens(initialScreen='start')
 
if __name__ == "__main__":  
    main()
