import pygame
import cv2
import mediapipe as mp
import math
import numpy as np
from collections import deque

pygame.init()
mp_hands = mp.solutions.hands

WEBCAM_WIDTH, WEBCAM_HEIGHT = 640, 480
WINDOW_WIDTH, WINDOW_HEIGHT = 1000, 700

window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Advanced Gesture Paint")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)
TRANSPARENT = (0, 0, 0, 0)

# Drawing surface and state
drawing_surface = pygame.Surface((WEBCAM_WIDTH, WEBCAM_HEIGHT), pygame.SRCALPHA)
drawing_surface.fill(TRANSPARENT)

# Global variables
current_color = RED
brush_size = 10
last_pinch_pos = None
drawing = False
drawing_mode = "pen"  # pen, spray, circle, square
undo_stack = deque(maxlen=20)
redo_stack = deque(maxlen=20)
last_surface = None
spray_particles = []
eraser_mode = False
rainbow_mode = False
rainbow_hue = 0

class Button:
    def __init__(self, x, y, width, height, color, text, font_size=16):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text = text
        self.font_size = font_size
        self.hover = False
    
    def draw(self, surface):
        color = self.color if not self.hover else tuple(min(255, c + 30) for c in self.color)
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)
        
        font = pygame.font.SysFont("Arial", self.font_size)
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class ColorButton(Button):
    def __init__(self, x, y, size, color, name):
        super().__init__(x, y, size, size, color, name, 12)
        self.color_value = color

# Create buttons
buttons = [
    Button(10, 10, 80, 30, RED, "Red"),
    Button(100, 10, 80, 30, GREEN, "Green"),
    Button(190, 10, 80, 30, BLUE, "Blue"),
    Button(280, 10, 80, 30, YELLOW, "Yellow"),
    Button(370, 10, 80, 30, PURPLE, "Purple"),
    Button(460, 10, 80, 30, CYAN, "Cyan"),
    Button(550, 10, 80, 30, ORANGE, "Orange"),
    Button(640, 10, 80, 30, PINK, "Pink"),
    Button(730, 10, 80, 30, BLACK, "Black"),
    Button(820, 10, 80, 30, (128, 128, 128), "Rainbow"),
    Button(10, 50, 80, 30, (100, 100, 100), "Eraser"),
    Button(100, 50, 80, 30, (150, 150, 150), "Pen"),
    Button(190, 50, 80, 30, (150, 150, 150), "Spray"),
    Button(280, 50, 80, 30, (150, 150, 150), "Circle"),
    Button(370, 50, 80, 30, (150, 150, 150), "Square"),
    Button(460, 50, 80, 30, (200, 200, 200), "Size +"),
    Button(550, 50, 80, 30, (200, 200, 200), "Size -"),
    Button(640, 50, 80, 30, (100, 100, 100), "Undo"),
    Button(730, 50, 80, 30, (100, 100, 100), "Redo"),
    Button(820, 50, 80, 30, (255, 100, 100), "Clear"),
]

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5)

def calculate_distance(lm1, lm2):
    return math.hypot(lm1.x - lm2.x, lm1.y - lm2.y)

def save_state():
    global undo_stack, last_surface
    if last_surface is not None:
        undo_stack.append(last_surface.copy())
    last_surface = drawing_surface.copy()

def undo():
    global drawing_surface, redo_stack, undo_stack
    if undo_stack:
        redo_stack.append(drawing_surface.copy())
        drawing_surface = undo_stack.pop()

def redo():
    global drawing_surface, redo_stack, undo_stack
    if redo_stack:
        undo_stack.append(drawing_surface.copy())
        drawing_surface = redo_stack.pop()

def hsv_to_rgb(h, s, v):
    h = h / 360.0
    c = v * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = v - c
    
    if h < 1/6:
        r, g, b = c, x, 0
    elif h < 2/6:
        r, g, b = x, c, 0
    elif h < 3/6:
        r, g, b = 0, c, x
    elif h < 4/6:
        r, g, b = 0, x, c
    elif h < 5/6:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))

def draw_spray(surface, pos, color, size):
    for _ in range(size * 2):
        offset_x = np.random.randint(-size, size)
        offset_y = np.random.randint(-size, size)
        if offset_x**2 + offset_y**2 <= size**2:
            spray_pos = (pos[0] + offset_x, pos[1] + offset_y)
            if 0 <= spray_pos[0] < WEBCAM_WIDTH and 0 <= spray_pos[1] < WEBCAM_HEIGHT:
                surface.set_at(spray_pos, color)

def draw_circle(surface, pos, color, size):
    pygame.draw.circle(surface, color, pos, size)

def draw_square(surface, pos, color, size):
    rect = pygame.Rect(pos[0] - size, pos[1] - size, size * 2, size * 2)
    pygame.draw.rect(surface, color, rect)

def main():
    global last_pinch_pos, drawing, current_color, drawing_surface
    global drawing_mode, brush_size, eraser_mode, rainbow_mode, rainbow_hue
    
    cap = cv2.VideoCapture(0)
    clock = pygame.time.Clock()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Handle button events
            for i, btn in enumerate(buttons):
                if btn.handle_event(event):
                    if i == 0:  # Red
                        current_color = RED
                        eraser_mode = False
                        rainbow_mode = False
                    elif i == 1:  # Green
                        current_color = GREEN
                        eraser_mode = False
                        rainbow_mode = False
                    elif i == 2:  # Blue
                        current_color = BLUE
                        eraser_mode = False
                        rainbow_mode = False
                    elif i == 3:  # Yellow
                        current_color = YELLOW
                        eraser_mode = False
                        rainbow_mode = False
                    elif i == 4:  # Purple
                        current_color = PURPLE
                        eraser_mode = False
                        rainbow_mode = False
                    elif i == 5:  # Cyan
                        current_color = CYAN
                        eraser_mode = False
                        rainbow_mode = False
                    elif i == 6:  # Orange
                        current_color = ORANGE
                        eraser_mode = False
                        rainbow_mode = False
                    elif i == 7:  # Pink
                        current_color = PINK
                        eraser_mode = False
                        rainbow_mode = False
                    elif i == 8:  # Black
                        current_color = BLACK
                        eraser_mode = False
                        rainbow_mode = False
                    elif i == 9:  # Rainbow
                        rainbow_mode = True
                        eraser_mode = False
                    elif i == 10:  # Eraser
                        eraser_mode = True
                        rainbow_mode = False
                    elif i == 11:  # Pen
                        drawing_mode = "pen"
                    elif i == 12:  # Spray
                        drawing_mode = "spray"
                    elif i == 13:  # Circle
                        drawing_mode = "circle"
                    elif i == 14:  # Square
                        drawing_mode = "square"
                    elif i == 15:  # Size +
                        brush_size = min(50, brush_size + 2)
                    elif i == 16:  # Size -
                        brush_size = max(1, brush_size - 2)
                    elif i == 17:  # Undo
                        undo()
                    elif i == 18:  # Redo
                        redo()
                    elif i == 19:  # Clear
                        save_state()
                        drawing_surface.fill(TRANSPARENT)

        success, frame = cap.read()
        if not success:
            continue
        
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)
        
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = pygame.image.frombuffer(frame.tobytes(), frame.shape[1::-1], "RGB")
        frame = pygame.transform.scale(frame, (WEBCAM_WIDTH, WEBCAM_HEIGHT))
        
        webcam_x = (WINDOW_WIDTH - WEBCAM_WIDTH) // 2
        webcam_y = 100  # Moved down to make room for buttons
        
        window.fill(WHITE)
        window.blit(frame, (webcam_x, webcam_y))
        window.blit(drawing_surface, (webcam_x, webcam_y))
        
        # Draw buttons
        for btn in buttons:
            btn.draw(window)
        
        # Draw info panel
        font = pygame.font.SysFont("Arial", 16)
        info_text = f"Mode: {drawing_mode.title()} | Size: {brush_size} | Color: {'Rainbow' if rainbow_mode else 'Eraser' if eraser_mode else 'Custom'}"
        text_surf = font.render(info_text, True, BLACK)
        window.blit(text_surf, (10, WINDOW_HEIGHT - 30))
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Get finger positions
            thumb = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            index = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
            ring = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
            pinky = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]
            
            # Convert to screen coordinates
            pinch_center = (
                int((thumb.x + index.x)/2 * WEBCAM_WIDTH),
                int((thumb.y + index.y)/2 * WEBCAM_HEIGHT))
            
            # Adjust for webcam position
            screen_pinch_center = (pinch_center[0] + webcam_x, pinch_center[1] + webcam_y)
            
            # Calculate distances
            pinch_distance = calculate_distance(thumb, index)
            middle_distance = calculate_distance(thumb, middle)
            ring_distance = calculate_distance(thumb, ring)
            pinky_distance = calculate_distance(thumb, pinky)
            
            # Draw hand position indicator
            pygame.draw.circle(window, (255, 0, 0), screen_pinch_center, 5)
            
            # Pinch gesture for drawing
            if pinch_distance < 0.05:
                if not drawing:
                    drawing = True
                    last_pinch_pos = pinch_center
                    save_state()
                
                if last_pinch_pos:
                    # Update rainbow color
                    if rainbow_mode:
                        current_color = hsv_to_rgb(rainbow_hue, 1, 1)
                        rainbow_hue = (rainbow_hue + 5) % 360
                    
                    # Choose drawing color
                    draw_color = WHITE if eraser_mode else current_color
                    
                    # Draw based on mode
                    if drawing_mode == "pen":
                        pygame.draw.line(drawing_surface, draw_color,
                                        last_pinch_pos, pinch_center,
                                        brush_size)
                    elif drawing_mode == "spray":
                        draw_spray(drawing_surface, pinch_center, draw_color, brush_size)
                    elif drawing_mode == "circle":
                        draw_circle(drawing_surface, pinch_center, draw_color, brush_size)
                    elif drawing_mode == "square":
                        draw_square(drawing_surface, pinch_center, draw_color, brush_size)
                
                last_pinch_pos = pinch_center
            else:
                drawing = False
                last_pinch_pos = None
            
            # Gesture controls
            # Middle finger + thumb = undo
            if middle_distance < 0.05 and not drawing:
                undo()
            
            # Ring finger + thumb = redo
            if ring_distance < 0.05 and not drawing:
                redo()
            
            # Pinky + thumb = clear
            if pinky_distance < 0.05 and not drawing:
                save_state()
                drawing_surface.fill(TRANSPARENT)
        
        pygame.display.flip()
        clock.tick(30)
    
    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()
