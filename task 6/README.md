# Object Counting (Flask + OpenCV)

Simple AI-powered app to count moving objects crossing a line in video files or live camera.

Quick start

1. Create a virtual environment and install requirements:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Run the app:

```bash
python app.py
```

3. Open http://localhost:5000 in your browser. Use "Live camera" or upload a video.

Notes
- Counting is implemented via background subtraction + simple centroid tracking.
- For better accuracy use a trained detector (YOLO/SSD) and a more robust tracker.
