# DrawingWithHands 🖐️🎨

A Python application that lets you draw in the air using hand gestures, powered by MediaPipe and Pygame.

## Features ✨
- Real-time hand tracking with 21 landmarks
- Pinch gesture detection for drawing
- Adjustable brush size and color
- Clear canvas functionality
- Webcam feed overlay

## Requirements 📋
- Python 3.11+
- Webcam

## Installation 🛠️

1. Clone the repository:
```bash
git clone https://github.com/yourusername/DrawWithHands.git
cd DrawWithHands
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage 🚀
Run the application:
```bash
python draw.py
```

### Controls:
- **Pinch gesture**: Draw on the canvas
- **Brush button**: Switch to red brush
- **Clear All button**: Reset the canvas
- **ESC**: Exit the application

## How It Works 🔍
The application uses:
- MediaPipe for real-time hand tracking
- Pygame for rendering and drawing
- Pinch detection between thumb and index finger
- Simple GUI buttons for controls

## Demo 📸
![Gesture Drawing Demo](gesture-recognizer.png)

## Troubleshooting ⚠️
- If webcam isn't detected, try changing `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)`
- For performance issues, reduce the webcam resolution
- Ensure proper lighting for better hand detection

