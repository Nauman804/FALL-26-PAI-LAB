from flask import Flask, render_template, Response, request, redirect, url_for
import os
import threading
from object_counter import VideoProcessor

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

video_processor = None
vp_lock = threading.Lock()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/live')
def live():
    return render_template('live.html')


def gen_live():
    global video_processor
    with vp_lock:
        if video_processor is None:
            video_processor = VideoProcessor(source=0)
        else:
            video_processor.set_source(0)
    for frame in video_processor.generate_frames():
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(gen_live(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('video')
    if not file:
        return 'No file provided', 400
    filename = file.filename
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)
    global video_processor
    with vp_lock:
        if video_processor:
            video_processor.release()
        video_processor = VideoProcessor(source=save_path)
    return redirect(url_for('uploaded_video'))


@app.route('/uploaded')
def uploaded_video():
    return render_template('upload_result.html')


@app.route('/upload_feed')
def upload_feed():
    global video_processor
    if video_processor is None:
        return 'No uploaded video processed yet', 400

    def gen():
        for frame in video_processor.generate_frames():
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
