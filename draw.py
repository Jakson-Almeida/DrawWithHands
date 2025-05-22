import pygame
import cv2
import mediapipe as mp
import math

pygame.init()
mp_hands = mp.solutions.hands

WEBCAM_WIDTH, WEBCAM_HEIGHT = 640, 480
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600

window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Simple Gesture Paint")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
TRANSPARENT = (0, 0, 0, 0)

drawing_surface = pygame.Surface((WEBCAM_WIDTH, WEBCAM_HEIGHT), pygame.SRCALPHA)
drawing_surface.fill(TRANSPARENT)

current_color = RED
brush_size = 10
last_pinch_pos = None
drawing = False

class Button:
    def __init__(self, x, y, width, height, color, text):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.text = text
    
    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        font = pygame.font.SysFont("Arial", 20)
        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

buttons = [
    Button(10, 10, 100, 40, RED, "Brush"),
    Button(120, 10, 100, 40, BLUE, "Clear All")
]

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.5)

def calculate_distance(lm1, lm2):
    return math.hypot(lm1.x - lm2.x, lm1.y - lm2.y)

def main():
    global last_pinch_pos, drawing, current_color, drawing_surface
    
    cap = cv2.VideoCapture(0)
    clock = pygame.time.Clock()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for btn in buttons:
                    if btn.rect.collidepoint(mouse_pos):
                        if btn.text == "Clear All":
                            drawing_surface.fill(TRANSPARENT)
                        elif btn.text == "Brush":
                            current_color = RED

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
        webcam_y = (WINDOW_HEIGHT - WEBCAM_HEIGHT) // 2
        
        window.fill(WHITE)
        window.blit(frame, (webcam_x, webcam_y))
        window.blit(drawing_surface, (webcam_x, webcam_y))
        
        for btn in buttons:
            btn.draw(window)
        
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            thumb = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            index = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
            
            pinch_center = (
                int((thumb.x + index.x)/2 * WEBCAM_WIDTH),
                int((thumb.y + index.y)/2 * WEBCAM_HEIGHT))
            
            distance = calculate_distance(thumb, index)
            
            if distance < 0.05:
                if not drawing:
                    drawing = True
                    last_pinch_pos = pinch_center
                
                if last_pinch_pos:
                    pygame.draw.line(drawing_surface, current_color,
                                    last_pinch_pos, pinch_center,
                                    brush_size)
                
                last_pinch_pos = pinch_center
            else:
                drawing = False
                last_pinch_pos = None
        
        pygame.display.flip()
        clock.tick(30)
    
    cap.release()
    pygame.quit()

if __name__ == "__main__":
    main()
