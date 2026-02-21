import cv2
import numpy as np


class VideoProcessor:
    def __init__(self, source=0, min_area=500):
        self.source = source
        self.cap = cv2.VideoCapture(source)
        self.bg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=25)
        self.min_area = min_area
        self.tracks = {}
        self.next_object_id = 0
        self.count = 0
        self.line_position = None
        self.max_disappeared = 30

    def set_source(self, source):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
        self.source = source
        self.cap = cv2.VideoCapture(source)
        self.bg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=25)
        self.tracks = {}
        self.next_object_id = 0
        self.count = 0

    def release(self):
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def generate_frames(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            frame = cv2.resize(frame, (640, 480))
            if self.line_position is None:
                self.line_position = frame.shape[0] // 2

            mask = self.bg.apply(frame)
            _, mask = cv2.threshold(mask, 254, 255, cv2.THRESH_BINARY)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            centers = []
            for c in contours:
                if cv2.contourArea(c) < self.min_area:
                    continue
                x, y, w, h = cv2.boundingRect(c)
                cx = int(x + w / 2)
                cy = int(y + h / 2)
                centers.append((cx, cy, x, y, w, h))

            self._update_tracks(centers)

            for obj_id, tr in self.tracks.items():
                (cx, cy) = tr['centroid']
                x, y, w, h = tr['bbox']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f'ID {obj_id}', (cx - 10, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (0, 255, 0), 2)

            cv2.line(frame, (0, self.line_position), (frame.shape[1], self.line_position), (0, 0, 255), 2)
            cv2.putText(frame, f'Count: {self.count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            ret2, jpeg = cv2.imencode('.jpg', frame)
            if not ret2:
                continue
            yield jpeg.tobytes()

        self.release()

    def _update_tracks(self, centers):
        if len(self.tracks) == 0:
            for c in centers:
                self.tracks[self.next_object_id] = {'centroid': (c[0], c[1]), 'bbox': (c[2], c[3], c[4], c[5]),
                                                    'disappeared': 0, 'last_positions': [c[1]]}
                self.next_object_id += 1
            return

        used_ids = set()
        for c in centers:
            cx, cy = c[0], c[1]
            min_dist = None
            min_id = None
            for obj_id, tr in self.tracks.items():
                if obj_id in used_ids:
                    continue
                tcx, tcy = tr['centroid']
                dist = (cx - tcx) ** 2 + (cy - tcy) ** 2
                if min_dist is None or dist < min_dist:
                    min_dist = dist
                    min_id = obj_id

            if min_id is not None and min_dist < 4000:
                tr = self.tracks[min_id]
                tr['centroid'] = (cx, cy)
                tr['bbox'] = (c[2], c[3], c[4], c[5])
                tr['disappeared'] = 0
                tr['last_positions'].append(cy)
                used_ids.add(min_id)
                lp = tr['last_positions']
                if len(lp) >= 2:
                    if lp[-2] < self.line_position <= lp[-1]:
                        self.count += 1
            else:
                self.tracks[self.next_object_id] = {'centroid': (cx, cy), 'bbox': (c[2], c[3], c[4], c[5]),
                                                    'disappeared': 0, 'last_positions': [cy]}
                self.next_object_id += 1

        for obj_id in list(self.tracks.keys()):
            if obj_id not in used_ids:
                self.tracks[obj_id]['disappeared'] += 1
                if self.tracks[obj_id]['disappeared'] > self.max_disappeared:
                    del self.tracks[obj_id]
