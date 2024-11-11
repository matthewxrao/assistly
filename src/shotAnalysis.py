from collections import deque

# Initialize variables for shot tracking
ball_positions = deque(maxlen=30)
shot_in_progress = False
made_shots = 0
missed_shots = 0

def check_shot(ball_bbox, rim_bbox):
    global shot_in_progress, made_shots, missed_shots
    
    if ball_bbox is not None:
        ball_center = ((ball_bbox[0] + ball_bbox[2]) // 2, (ball_bbox[1] + ball_bbox[3]) // 2)
        ball_positions.append(ball_center)
    
    if len(ball_positions) < 2:
        return
    
    # Detect if ball is moving upwards for a shot attempt
    if not shot_in_progress and ball_positions[-1][1] < ball_positions[-2][1]:
        shot_in_progress = True
    
    # Detect if the ball enters or misses the rim
    if shot_in_progress and rim_bbox is not None:
        rim_center = ((rim_bbox[0] + rim_bbox[2]) // 2, (rim_bbox[1] + rim_bbox[3]) // 2)
        
        # Ball is within the rim's bounding box
        if (rim_bbox[0] <= ball_center[0] <= rim_bbox[2]) and (rim_bbox[1] <= ball_center[1] <= rim_bbox[3]):
            made_shots += 1
            shot_in_progress = False
            ball_positions.clear()
        
        # Ball falls below the rim after missing
        elif ball_positions[-1][1] > rim_bbox[3]:
            missed_shots += 1
            shot_in_progress = False
            ball_positions.clear()
