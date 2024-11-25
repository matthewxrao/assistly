import math
import random
from cmu_graphics import drawLine, rgb, drawRect
import time

# Creates a single lightning bolt
class LightningStrike:
    def __init__(self, x, y, max_length, duration, lean_direction):
        self.x = x
        self.y = y
        self.max_length = max_length
        self.duration = duration
        self.lean_direction = lean_direction
        self.start_time = None
        self.active = False
        self.progress = 0.0
        self.branches = []
        self.flash_opacity = 0
        self.hue_offset = random.uniform(0, 1)
        self.generate_strike_pattern()
    
    def generate_strike_pattern(self):
        self.branches = []
        def recursive_branch(x, y, angle, length, depth, is_main_bolt=False):
            if depth <= 0 or length < 2:
                return
            
            # Main bolt gets less randomness than branches
            if is_main_bolt:
                base_jitter = random.uniform(-20, 20)  # Reduced jitter
                jitter = base_jitter + (self.lean_direction * random.uniform(5, 15))
            else:
                jitter = random.uniform(-45, 45)  # Reduced branch angle
            
            segments = []
            current_x, current_y = x, y
            num_segments = random.randint(3, 4) if is_main_bolt else random.randint(2, 3)  # Fewer segments
            segment_length = length / num_segments
            
            last_angle = angle
            for _ in range(num_segments):
                micro_jitter = random.uniform(-10, 10) if is_main_bolt else random.uniform(-15, 15)  # Reduced micro-jitter
                last_angle = last_angle + micro_jitter * 0.6  # Reduced angle change
                angle_rad = math.radians(last_angle + jitter)
                
                actual_length = segment_length * random.uniform(0.9, 1.1)  # Less length variation
                end_x = current_x + actual_length * math.cos(angle_rad)
                end_y = current_y + actual_length * math.sin(angle_rad)
                
                end_x = max(10, min(670, end_x))
                end_y = max(10, min(410, end_y))
                
                segments.append({
                    'start': (current_x, current_y),
                    'end': (end_x, end_y),
                    'depth': depth,
                    'is_main': is_main_bolt
                })
                
                # Create branch forks from main bolt
                if is_main_bolt:
                    if length > self.max_length * 0.15:
                        num_branches = random.randint(1, 2)  # Fewer branches
                        for _ in range(num_branches):
                            if random.random() < 0.7:  # Reduced branch probability
                                branch_angle = last_angle + random.uniform(-60, 60)
                                branch_length = length * random.uniform(0.3, 0.5)  # Shorter branches
                                recursive_branch(current_x, current_y, branch_angle, 
                                              branch_length, depth - 1, False)
                
                current_x, current_y = end_x, end_y
                jitter = random.uniform(-20, 20)
            
            self.branches.extend(segments)
            
            # Create smaller sub-branches
            if not is_main_bolt and depth > 1 and length > 25:  # Increased length threshold
                if random.random() < 0.5:  # Reduced probability
                    angle_var = random.uniform(30, 60)  # Reduced angle variation
                    if random.random() < 0.5:
                        angle_var *= -1
                    
                    branch_length = length * random.uniform(0.3, 0.6)  # Shorter branches
                    recursive_branch(
                        current_x, current_y,
                        last_angle + angle_var,
                        branch_length,
                        depth - 1,
                        False
                    )
        
        # Pick random start point and angle
        if self.lean_direction > 0:
            start_x = random.randint(0, 100)
        else:
            start_x = random.randint(550, 650)
            
        base_angle = 90 + random.uniform(-15, 15)
        start_angle = base_angle + (self.lean_direction * random.uniform(5, 10))
        recursive_branch(start_x, 10, start_angle, self.max_length, 5, True)  # Reduced depth

    # Generate shifting RGB colors
    def get_rgb_color(self, time_offset, saturation):
        t = (time.time() * 1.5 + time_offset + self.hue_offset) % 1  # Slower color cycling
        
        if t < 1/6:
            r, g, b = 1, t*6, 0
        elif t < 2/6:
            r, g, b = (2-t*6), 1, 0
        elif t < 3/6:
            r, g, b = 0, 1, (t*6-2)
        elif t < 4/6:
            r, g, b = 0, (4-t*6), 1
        elif t < 5/6:
            r, g, b = (t*6-4), 0, 1
        else:
            r, g, b = 1, 0, (6-t*6)
        
        flicker = random.uniform(0.95, 1.05)  # Reduced flicker
        r = int(min(255, (r * saturation + (1 - saturation)) * 255 * flicker))
        g = int(min(255, (g * saturation + (1 - saturation)) * 255 * flicker))
        b = int(min(255, (b * saturation + (1 - saturation)) * 255 * flicker))
        
        return rgb(r, g, b)

    # Start the lightning animation
    def start(self, current_time):
        self.start_time = current_time
        self.active = True
        self.progress = 0.0
        self.flash_opacity = 0
        self.generate_strike_pattern()

    # Update lightning progress and flash effects
    def update(self, current_time):
        if not self.active:
            return

        elapsed = current_time - self.start_time
        strike_duration = self.duration * 0.4
        flash_duration = self.duration * 0.6
        
        if elapsed > self.duration:
            self.active = False
            return

        if elapsed <= strike_duration:
            t = elapsed / strike_duration
            self.progress = 1 - (1 - t) * (1 - t)
            self.flash_opacity = 0
        else:
            self.progress = 1
            flash_elapsed = elapsed - strike_duration
            flash_t = flash_elapsed / flash_duration
            
            flash_progress = 1 - flash_t
            self.flash_opacity = int(15 * flash_progress * (1 + math.sin(flash_progress * 10)))  # Reduced flash

    # Draw the lightning bolt
    def draw(self):
        if not self.active:
            return

        if self.flash_opacity > 0:
            flash_color = self.get_rgb_color(0.8, 0.6)  # Reduced saturation
            drawRect(0, 0, 650, 450, fill=flash_color, opacity=self.flash_opacity)

        total_branches = len(self.branches)
        visible_branches = int(total_branches * self.progress)
        
        for i, branch in enumerate(self.branches[:visible_branches]):
            branch_progress = min(1.0, (visible_branches - i) / 2)
            if branch_progress <= 0:
                continue

            start_x, start_y = branch['start']
            end_x, end_y = branch['end']
            depth = branch['depth']
            is_main = branch['is_main']
            
            current_end_x = start_x + (end_x - start_x) * branch_progress
            current_end_y = start_y + (end_y - start_y) * branch_progress
            
            self.draw_lightning_segment(
                start_x, start_y,
                current_end_x, current_end_y,
                depth, branch_progress, is_main
            )

    # Draw multi-layered glow effect
    def draw_lightning_segment(self, x1, y1, x2, y2, depth, intensity, is_main):
        max_glow = 10 if is_main else 7  # Reduced glow size
        
        # Outer glow
        opacity = int(15 * intensity)  # Reduced opacity
        color = self.get_rgb_color(0.2, 0.7)  # Less saturated
        glow_width = max_glow * (1.2 if is_main else 0.9)
        drawLine(x1, y1, x2, y2, fill=color, opacity=opacity, lineWidth=glow_width)
        
        # Middle glow
        opacity = int(20 * intensity)
        color = self.get_rgb_color(0.4, 0.8)
        glow_width = (max_glow-3) * (0.8 if is_main else 0.6)
        drawLine(x1, y1, x2, y2, fill=color, opacity=opacity, lineWidth=glow_width)
        
        # Inner glow
        opacity = int(25 * intensity)
        color = self.get_rgb_color(0.6, 0.9)
        glow_width = (max_glow-6) * (0.6 if is_main else 0.4)
        drawLine(x1, y1, x2, y2, fill=color, opacity=opacity, lineWidth=glow_width)
        
        # White core
        drawLine(x1, y1, x2, y2, fill='white', lineWidth=2 if is_main else 1)  # Thinner core

# Initialize multiple lightning bolts
def init_fissure(app):
    app.fissures = [
        LightningStrike(
            app.width * 0.2,
            10,
            max_length=app.height * 0.9, 
            duration=0.5,
            lean_direction=1
        ),
        LightningStrike(
            app.width * 0.4,
            10,
            max_length=app.height * 0.9,
            duration=0.5,
            lean_direction=-0.5
        ),
        LightningStrike(
            app.width * 0.6,
            10,
            max_length=app.height * 0.3,
            duration=0.5,
            lean_direction=1
        ),
        LightningStrike(
            app.width * 0.6,
            10,
            max_length=app.height * 0.4,
            duration=0.5,
            lean_direction=0.5
        ),
        LightningStrike(
            app.width * 0.6,
            10,
            max_length=app.height * 0.3,
            duration=0.5,
            lean_direction=0.5
        ),
        LightningStrike(
            app.width * 0.6,
            10,
            max_length=app.height * 0.4,
            duration=0.5,
            lean_direction=-1
        ),
    ]
    app.strike_delays = [0, 0.3, 0.06, 0.09, 0.12, 0.15]

# Start all lightning strikes with delays
def trigger_fissure(app, current_time):
    for i, fissure in enumerate(app.fissures):
        fissure.start(current_time + app.strike_delays[i])

# Update all active lightning strikes
def update_fissure(app, current_time):
    for fissure in app.fissures:
        fissure.update(current_time)

# Draw all active lightning strikes
def draw_fissure(app):
    for fissure in app.fissures:
        fissure.draw()