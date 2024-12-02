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

#|************************| INITIALIZE APP |************************|#

def onAppStart(app):
    app.width = 650
    app.height = 460
    
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
    
    # Initialize shot tracking stats and streaks
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
    app.crowd = 'humans'
    app.crowdSound = Sound(getCrowdNoise(app.crowd))
    app.background = rgb(23, 23, 23)
    app.setMaxShapeCount(10000)

    app.frameQueue = queue.Queue()
    app.ballDetectionPersistenceThreshold = 40
    app.rimDetectionPersistenceThreshold = 20
    app.shotMadePersistenceThreshold = 20

    app.ballDetectionCounter = app.ballDetectionPersistenceThreshold  
    app.rimDetectionCounter = app.rimDetectionPersistenceThreshold
    app.shotMadeDetectionCounter = app.shotMadePersistenceThreshold

    # Stats Variables
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
    
    # Shot history panel dimensions
    app.historyLeft = app.camFeedOutlineLeft + (app.camFeedOutlineWidth - 200) + 20
    app.historyTop = app.camFeedOutlineTop + 30
    app.historyWidth = 200
    app.historyHeight = 150
    app.currentTab = 'liveView'
    visualEffects.init_fissure(app)
    setSoundButtons(app)
    setTabButtons(app)


def setTabButtons(app):
    # Initialize buttons dictionary with screen-specific button coordinates
    spacing = 10
    buttonWidth = (app.camFeedOutlineWidth - 2 * spacing) // 3
    startX = app.camFeedOutlineLeft
    
    app.buttons = {
        'continue': {
            'left': app.width//2 - 65,
            'top': (app.height//2 + 105),
            'right': app.width//2 + 65,
            'bottom': (app.height//2 + 125),
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

# Converts frame to image URL displayable through CMU Graphics
def convert_frame_to_url(frame):
    temp_path = "tempFrame.jpg"
    cv2.imwrite(temp_path, frame)
    return temp_path

#|************************| APP FUNCTIONS |************************|#
def drawTabButtons(app):
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

def tabHover(app, x, y):
    for name, coords in app.buttons.items():
        if name == "continue":
            continue
        if (coords['left'] <= x <= coords['right'] and 
            coords['top'] <= y <= coords['bottom']):
            if name != app.currentTab:
                coords["opacity"] = 80
        else:
            coords["opacity"] = 100

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
                app.shotHistory.append((app.totalShots, True, time.time()))
                updateShotPercentage(app)
                updateStreak(app, True)
                triggerEffects(app)
        else:
            app.shotMadeDetectionCounter += 1

        app.ballStatus = app.ballDetectionCounter < app.ballDetectionPersistenceThreshold
        app.rimStatus = app.rimDetectionCounter < app.rimDetectionPersistenceThreshold
        app.shotMade = app.shotMadeDetectionCounter < app.shotMadePersistenceThreshold

        app.frameImage = convert_frame_to_url(frame_with_detections)
        updateStats(app)
        step(app)
        visualEffects.update_fissure(app, time.time())

def step(app):
    app.steps += 1
    if app.steps % 10 == 0:
        app.crowdSound = Sound(getCrowdNoise(app.crowd))

def updateStats(app):
    currentTime = time.time()
    elapsedMinutes = (currentTime - app.sessionStartTime) / 60
    
    if app.totalShots > 0:
        percentage = (app.madeShots / app.totalShots) * 100
        if len(app.graphPoints) == 0:
            # First shot
            app.graphPoints.append((elapsedMinutes, percentage, app.totalShots))
        elif app.totalShots > app.graphPoints[-1][2]:
            # New shot - add the point
            app.graphPoints.append((elapsedMinutes, percentage, app.totalShots))
        else:
            lastPoint = app.graphPoints[-1]
            app.graphPoints[-1] = (elapsedMinutes, lastPoint[1], lastPoint[2])

def simulateShotMade(app):
    app.shotMade = True
    app.madeShots += 1
    app.totalShots += 1
    app.shotHistory.append((app.totalShots, True, time.time()))
    updateShotPercentage(app)
    updateStreak(app, True)
    visualEffects.update_fissure(app, time.time())
    app.crowdSound = Sound(getCrowdNoise(app.crowd))
    triggerEffects(app)
    updateStats(app)
    step(app)

def simulateShotMissed(app):
    app.totalShots += 1
    app.shotHistory.append((app.totalShots, False, time.time()))
    app.currentStreak = 0
    updateShotPercentage(app)
    updateStreak(app, False)
    updateStats(app)
    visualEffects.update_fissure(app, time.time())
    step(app)

def triggerEffects(app):
    current_time = time.time()
    visualEffects.trigger_fissure(app, current_time)
    app.crowdSound.play(restart=False, loop=False)

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


#|************************| START SCREEN |************************|#

def start_onMousePress(app, x, y):
    setActiveScreen('tip')

def start_redrawAll(app):
    centerX, centerY = app.width // 2, app.height // 2
    left, top = (app.width - 350) // 2, (app.height - 350) // 2

    drawImage("images/logo.png", left, top)
    drawLabel(app.message, centerX, centerY + 75, size=20, fill='white', bold=True)

#|************************| TIP SCREEN |************************|#


def tip_onScreenActivate(app):
    app.message = "I UNDERSTAND IT NOW"

def tip_onMousePress(app, x, y):
    continueButton = app.buttons['continue']
    if (continueButton['left'] <= x <= continueButton['right'] and 
        continueButton['top'] <= y <= continueButton['bottom']):
        app.sessionStartTime = time.time()
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

    fps = cam.get(cv2.CAP_PROP_FPS)
    # Initialize EKF for ball tracking
    ekf = ExtendedKalmanFilter(dt=fps,  # Assuming 30 FPS
                            process_noise_std=1.0,
                            measurement_noise_std=10.0)

    while True:
        ret, frame = cam.read()
        if not ret:
            break
        
        frameX, frameY = app.camFeedWidth, app.camFeedHeight
        ballDetected, rimDetected, shotMadeDetected, frame_with_detections = detectObjects(frame, frameX, frameY, ekf)
        app.frameQueue.put((ballDetected, rimDetected, shotMadeDetected, frame_with_detections))
        
    cam.release()
        

def tip_redrawAll(app):
    centerX, y = app.width // 2, (app.height // 2) + 115
    drawAssets(app)
    drawLabel("TIP", centerX, 65, size=15, fill='white', bold=True)
    drawImage("images/tip.png", centerX - 125, 75, width=250, height=250)
    drawLabel("For best detection results ensure the camera is at an angle", centerX, y - 50, size=12, bold=True, align='center', fill='white')
    drawLabel("between 30 - 45 degrees to the basket", centerX, y - 35, size=12, bold=True, align='center', fill='white')
    drawContinueButton(app, centerX, y)
    

def drawContinueButton(app, x, y):
    continueButton = app.buttons['continue']
    drawRect(continueButton['left'], continueButton['top'], 
            continueButton['right'] - continueButton['left'], 
            continueButton['bottom'] - continueButton['top'], 
            fill="white",
            opacity=continueButton['opacity'])
    
    drawLabel(app.message, x, y, size=10, fill=app.background, bold=True, align="center")

#|************************| LIVEVIEW SCREEN |************************|#

def liveView_onScreenActivate(app):
    app.currentTab = 'liveView'
    app.message = 'NO CAMERA INPUT'

def liveView_onKeyPress(app, key):
    if key == 'm': 
        simulateShotMade(app)
    elif key == 's':
        simulateShotMissed(app)

def liveView_onMousePress(app, x, y):
    tabPress(app, x, y)

def liveView_onMouseMove(app, x, y):
    tabHover(app, x, y)


def liveView_onStep(app):
    takeStep(app)

def liveView_redrawAll(app):
    drawAssets(app)
    drawTabButtons(app)
    drawCameraFeed(app)
    drawShotStats(app)

def drawCurrentStreak(app):
   x = app.camFeedOutlineLeft + 378
   y = app.height - 77
   
   if app.currentStreak < 3:
       drawImage("images/nostreak.png", x, y, width=64, height=64, opacity=100)
   else:
       hotstreak_files = list(pathlib.Path('images/hotstreak').glob('*.png'))
       hotstreak_path = random.choice(hotstreak_files)
       drawImage(str(hotstreak_path), x+2, y - 5, width=60, height=60, opacity=100)

def drawBestStreak(app):
    drawImage("images/beststreak.png", app.camFeedOutlineLeft + 485, app.height - 75, width=60, height=60, opacity=100)

# Draw shot stats and streak counters at the bottom of the screen
def drawShotStats(app):
    # Draw basic shot stats
    statsY = app.height - 45
    drawLabel(f"{app.madeShots}", 
             app.camFeedOutlineLeft + 20, statsY + 2, 
             size=35, bold=True, align="center", fill='white')
    
    drawLabel("MADE", app.camFeedOutlineLeft + 20, statsY + 30, size=8, bold=True, fill='white')
    
    drawLabel(f"{app.totalShots}", 
             app.camFeedOutlineLeft + 110, statsY + 2, 
             size=35, bold=True, align="center", fill='white')
    drawLabel("ATTEMPTS", app.camFeedOutlineLeft + 110, statsY + 30, size=8, bold=True, fill='white')

    drawLabel(f"{app.shotPercentage:.1f}%", 
             app.camFeedOutlineLeft + 210, statsY + 2, 
             size=35, bold=True, align="center", fill='white')
    drawLabel("FG PERCENTAGE", app.camFeedOutlineLeft + 210, statsY + 30, size=8, bold=True, fill='white')
    
    currentStreakText = 'orangeRed' if app.currentStreak >= 3 else 'black'
    drawCurrentStreak(app)
    drawLabel(f"{app.currentStreak}", 
             app.camFeedOutlineLeft + 410, statsY, 
             size=30, bold=True, align="center", fill=currentStreakText)
    drawLabel("CURRENT STREAK", app.camFeedOutlineLeft + 410, statsY + 30, size=8, bold=True, fill='white')
    
    drawBestStreak(app)
    drawLabel(f"{app.bestStreak}", 
             app.camFeedOutlineLeft + 515, statsY, 
             size=30, bold=True, align="center", fill='darkslateblue')
    drawLabel("BEST STREAK", app.camFeedOutlineLeft + 515, statsY + 30, size=8, bold=True, fill='white')

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
    drawLabel(ballStatusText, ballStatusX - 12, statusY, bold=True, size=10, align="right", fill='white')
    
    drawRect(app.camFeedOutlineLeft, app.camFeedOutlineTop, app.camFeedOutlineWidth, app.camFeedOutlineHeight, fill=outlineColor)
    drawLabel(rimStatusText, app.camFeedOutlineLeft + 5, statusY, size=10, bold=True, align="left", fill='white')

    if app.frameImage is not None:
        drawImage(app.frameImage, app.camFeedLeft, app.camFeedTop)
    else:
        drawRect(app.camFeedLeft, app.camFeedTop, app.camFeedWidth, app.camFeedHeight, fill=app.background)
        drawLabel(app.message, centerX, centerY, size=12, bold=True, fill='white')
    
#|************************| STATS SCREEN |************************|#

def stats_onScreenActivate(app):
    app.currentTab = 'stats'

def stats_onStep(app):
    takeStep(app)

def stats_onKeyPress(app, key):
    if key == 'm': 
        simulateShotMade(app)
    elif key == 's':
        simulateShotMissed(app)

def stats_onMousePress(app, x, y):
    tabPress(app, x, y)

def stats_onMouseMove(app, x, y):
    tabHover(app, x, y)
    currentTime = time.time()
    elapsedMinutes = (currentTime - app.sessionStartTime) / 60
    timeWindow = max(elapsedMinutes, app.minGraphMinutes)
    
    app.hoveredPoint = None
    for i, point in enumerate(app.graphPoints):
        pointX = app.graphLeft + (point[0] / timeWindow) * app.graphWidth
        pointY = app.graphTop + app.graphHeight - (point[1]/100 * app.graphHeight)
        
        # Check if mouse is within 10 pixels of point
        if ((x - pointX)**2 + (y - pointY)**2) <= 100:  # Using 100 as threshold (10^2)
            app.hoveredPoint = i
            break

def formatTimeLabel(minutes):
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
    totalSeconds = int(minutes * 60)
    mins = totalSeconds // 60
    secs = totalSeconds % 60
    if secs < 10:
        secs = f"0{secs}"
    if mins < 10:
        mins = f"0{mins}"
    return f"{mins}:{secs}"

def drawInfoBox(app, x, y, pointIndex, percentage, made, total):
    boxWidth = 80
    boxHeight = 75
    padding = 10
    
    boxLeft = min(x - boxWidth/2, app.graphLeft + app.graphWidth - boxWidth - padding)
    boxTop = min(y - boxHeight - padding, app.graphTop + app.graphHeight - boxHeight + padding)
    if boxTop < app.graphTop:
        boxTop = y + padding

    _, make, timestamp = app.shotHistory[pointIndex - 1]
    timestamp = formatTimeHeader((timestamp - app.sessionStartTime) / 60)
    outlineColor = 'limegreen' if make else 'crimson'
    drawRect(boxLeft, boxTop, boxWidth, boxHeight, 
            fill=app.background, opacity=90, border=outlineColor)


    textY = boxTop + 12
    drawLabel(f"SHOT {total}",
            boxLeft + boxWidth/2, textY,
            fill='white', size=12, bold=True)

    textY += 15
    drawLabel(f"MADE: {made}",
             boxLeft + boxWidth/2, textY,
             fill='white', size=9)
    textY += 12
    drawLabel(f"MISSED: {total - made}",
             boxLeft + boxWidth/2, textY,
             fill='white', size=9)
    textY += 12
    drawLabel(f"FG %: {percentage:.1f}%",
             boxLeft + boxWidth/2, textY,
             fill='white', size=9)
    textY += 12
    drawLabel(f"{timestamp}",
             boxLeft + boxWidth/2, textY,
             fill='white', size=9, bold=True)

def drawPoint(app, x, y, isHovered, isCurrent=False):
    baseRadius = 5
    if isHovered:
        # Draw shadow
        drawCircle(x+1, y+1, baseRadius+2, fill='gray', opacity=40)
        drawCircle(x, y, baseRadius+2, fill='white')
    else:
        drawCircle(x, y, baseRadius, fill='white')

def drawGraph(app):
    currentTime = time.time()
    elapsedMinutes = (currentTime - app.sessionStartTime) / 60
    timeWindow = max(elapsedMinutes, app.minGraphMinutes)
    
    drawRect(app.graphLeft, app.graphTop, app.graphWidth, app.graphHeight, 
             fill=None, border='white')
    
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
    
    for i in range(0, 101, 20):
        y = app.graphTop + app.graphHeight - (i/100 * app.graphHeight)
        drawLabel(f"{i}%", app.graphLeft - 10, y, 
                 fill='white', bold=True, size=10, align='right')
        drawLine(app.graphLeft, y, app.graphLeft + app.graphWidth, y,
                fill='gray', opacity=30)
    
    if len(app.graphPoints) > 0:
        x0 = app.graphLeft
        x1 = app.graphLeft + (app.graphPoints[0][0] / timeWindow) * app.graphWidth
        y1 = app.graphTop + app.graphHeight - (app.graphPoints[0][1]/100 * app.graphHeight)
        drawLine(x0, y1, x1, y1, fill='lightBlue', lineWidth=2)
        drawPoint(app, x1, y1, app.hoveredPoint == 0)

        fx, fy, fi = 0, 0, 0
        
        for i in range(len(app.graphPoints)-1):
            x1 = app.graphLeft + (app.graphPoints[i][0] / timeWindow) * app.graphWidth
            y1 = app.graphTop + app.graphHeight - (app.graphPoints[i][1]/100 * app.graphHeight)
            x2 = app.graphLeft + (app.graphPoints[i+1][0] / timeWindow) * app.graphWidth
            y2 = app.graphTop + app.graphHeight - (app.graphPoints[i+1][1]/100 * app.graphHeight)
            
            drawLine(x1, y1, x2, y2, fill='lightBlue', lineWidth=2)
            drawPoint(app, x1, y1, app.hoveredPoint == i)
            
            if app.hoveredPoint == i:
                fx, fy, fi = x1, y1, i
        
        lastX = app.graphLeft + (app.graphPoints[-1][0] / timeWindow) * app.graphWidth
        lastY = app.graphTop + app.graphHeight - (app.graphPoints[-1][1]/100 * app.graphHeight)
        currentX = app.graphLeft + (elapsedMinutes / timeWindow) * app.graphWidth
        
        drawLine(lastX, lastY, currentX, lastY, fill='lightBlue', lineWidth=2)
        isLastPointHovered = app.hoveredPoint == len(app.graphPoints)-1
        drawPoint(app, lastX, lastY, isLastPointHovered)
        
        if app.hoveredPoint is None:
            drawInfoBox(app, lastX, lastY, len(app.graphPoints), 
                       app.shotPercentage, app.madeShots, app.totalShots)
        elif app.hoveredPoint is not None and not isLastPointHovered:
            madeShots = int((app.graphPoints[fi][1] / 100) * app.graphPoints[fi][2])
            drawInfoBox(app, fx, fy, fi+1, app.graphPoints[fi][1], 
                          madeShots, app.graphPoints[fi][2])
        elif isLastPointHovered:
            drawInfoBox(app, lastX, lastY, len(app.graphPoints),
                       app.shotPercentage, app.madeShots, app.totalShots)

def drawShotHistory(app):
    currentTime = time.time()
    elapsedMinutes = (currentTime - app.sessionStartTime) / 60

    drawLabel(f"TIME ELAPSED",
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
    for i, (shotNum, wasMade, timestamp) in enumerate(lastShots):
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
    drawLabel(f"SHOT HISTORY",
             app.historyLeft + app.historyWidth/2,
             app.historyTop + 45,
             bold=True,
             fill=app.background, size=12)
    
    drawRect(app.historyLeft + 20, startY - 20, shotWidth, app.camFeedOutlineHeight - 64, fill=None, border='white')
    
def stats_redrawAll(app):
    drawAssets(app)
    drawTabButtons(app)
    
    # Draw graph and history panels
    drawGraph(app)
    drawShotHistory(app)

#|************************| SOUNDS SCREEN |************************|#

def sounds_onScreenActivate(app):
    app.currentTab = 'sounds'

def drawSoundButtons(app):
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
    for name, coord, in app.soundButtons.items():
        if (coord['left'] <= x <= coord['right'] and 
            coord['top'] <= y <= coord['bottom']) and name != app.crowd:
            coord['opacity'] = 100
        elif name == app.crowd:
            coord['opacity'] = 100
        else:
            coord['opacity'] = 60

def soundButtonPress(app, x, y):
    for name, coord in app.soundButtons.items():
        if (coord['left'] <= x <= coord['right'] and 
            coord['top'] <= y <= coord['bottom']):
            app.crowd = name
            app.crowdSound = Sound(getCrowdNoise(app.crowd))

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

def main():
    runAppWithScreens(initialScreen='start')
 
if __name__ == "__main__":  
    main()