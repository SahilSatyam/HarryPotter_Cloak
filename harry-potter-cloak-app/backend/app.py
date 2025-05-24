from flask import Flask, Response, jsonify
import cv2
import numpy as np
import time
import threading

app = Flask(__name__)

# Global variables / Application context
camera_thread = None # Will hold the CameraThread instance
camera_lock = threading.Lock() # To manage access to camera_thread and shared resources
background_frame = None
is_camera_active = False # Indicates if the camera system is supposed to be running

# Kernels and color bounds (remains the same)
kernels = {
    'open': np.ones((10, 10), np.uint8),
    'close': np.ones((10, 10), np.uint8),
    'dilation': np.ones((10, 10), np.uint8)
}
color_bounds = {
    'lower': np.array([90, 50, 50]), 
    'upper': np.array([130, 255, 255])
}

class CameraThread(threading.Thread):
    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self.cap = None
        self.latest_jpeg_frame = None
        self.raw_frame_for_capture = None # For background capture
        self.frame_lock = threading.Lock() # To protect latest_jpeg_frame and raw_frame_for_capture
        self.stop_event = threading.Event() # For gracefully stopping the thread
        self.daemon = True # Allows main program to exit even if this thread is running

    def run(self):
        global background_frame # Allow modification of global background_frame
        print(f"CameraThread: Attempting to open camera at index {self.camera_index}...")
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print(f"CameraThread: Error: Could not open video device at index {self.camera_index}.")
            self.cap = None
            return

        print(f"CameraThread: Camera opened successfully at index {self.camera_index}.")
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                print("CameraThread: Error reading frame, stopping.")
                break
            
            # Store raw frame for background capture if needed
            with self.frame_lock:
                self.raw_frame_for_capture = frame.copy()

            # Process the frame (cloak effect)
            processed_frame = process_frame_logic(frame) # Uses global background_frame

            # Encode processed frame to JPEG
            (flag, encoded_image) = cv2.imencode(".jpg", processed_frame)
            if not flag:
                print("CameraThread: JPEG encoding failed.")
                continue
            
            with self.frame_lock:
                self.latest_jpeg_frame = bytearray(encoded_image)
            
            time.sleep(0.03) # ~30 FPS, adjust as needed, or remove if camera.read() is sufficiently blocking

        # Release camera when thread stops
        if self.cap:
            self.cap.release()
            self.cap = None
        print("CameraThread: Stopped and camera released.")

    def stop(self):
        print("CameraThread: Stop event set.")
        self.stop_event.set()

    def get_jpeg_frame(self):
        with self.frame_lock:
            if self.latest_jpeg_frame:
                return self.latest_jpeg_frame
            return None # Or a placeholder image bytes

    def get_raw_frame(self):
        with self.frame_lock:
            if self.raw_frame_for_capture is not None:
                return self.raw_frame_for_capture.copy() # Return a copy
            return None

def filter_mask_logic(mask):
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernels['open'])
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernels['close'])
    mask = cv2.dilate(mask, kernels['dilation'], iterations=1)
    return mask

def process_frame_logic(frame):
    global background_frame # Uses the global background_frame
    if background_frame is None:
        cv2.putText(frame, "BG Not Captured", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
        return frame

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, color_bounds['lower'], color_bounds['upper'])
    mask = filter_mask_logic(mask)
    mask_inv = cv2.bitwise_not(mask)
    cloak_part = cv2.bitwise_and(frame, frame, mask=mask_inv)
    background_part = cv2.bitwise_and(background_frame, background_frame, mask=mask)
    combined_frame = cv2.addWeighted(cloak_part, 1, background_part, 1, 0)
    return combined_frame

@app.route('/start_camera', methods=['POST'])
def start_camera_route():
    global camera_thread, is_camera_active
    with camera_lock:
        if camera_thread is not None and camera_thread.is_alive():
            return jsonify({"status": "success", "message": "Camera already running"}), 200
        
        # camera_index = 0 # Or get from request: request.json.get('camera_index', 0)
        camera_thread = CameraThread(camera_index=0)
        camera_thread.start()
        # Give the thread a moment to initialize the camera
        time.sleep(1) # Adjust as needed, or implement a more robust check

        if camera_thread.cap is None or not camera_thread.cap.isOpened():
             # Thread started but camera failed to open
            camera_thread.stop()
            camera_thread.join() # Wait for it to clean up
            camera_thread = None
            is_camera_active = False
            return jsonify({"status": "error", "message": "Failed to open camera within thread"}), 500
            
        is_camera_active = True
        return jsonify({"status": "success", "message": "Camera started"}), 200

@app.route('/stop_camera', methods=['POST'])
def stop_camera_route():
    global camera_thread, is_camera_active
    with camera_lock:
        if camera_thread is None or not camera_thread.is_alive():
            is_camera_active = False # Ensure state is consistent
            return jsonify({"status": "success", "message": "Camera already stopped"}), 200
        
        camera_thread.stop()
        camera_thread.join(timeout=5) # Wait for thread to finish

        if camera_thread.is_alive():
            print("Error: CameraThread did not stop in time. Resources may not be fully released.")
            # Attempt to aggressively clear the thread object, though the thread itself is still running
            camera_thread = None 
            is_camera_active = False # Mark as inactive
            return jsonify({"status": "error", "message": "Camera thread did not stop cleanly. Manual check may be required."}), 500
        
        camera_thread = None
        is_camera_active = False
        # global background_frame # Decide if background should be cleared on stop
        # background_frame = None 
    return jsonify({"status": "success", "message": "Camera stopped and resources released"}), 200

@app.route('/capture_background', methods=['POST'])
def capture_background_route():
    global background_frame, camera_thread, is_camera_active
    
    with camera_lock: # Ensure camera_thread object itself is not changed during this
        if not is_camera_active or camera_thread is None or not camera_thread.is_alive() or camera_thread.cap is None:
            return jsonify({"status": "error", "message": "Camera not running or not initialized. Start camera first."}), 400
    
    # No lock needed for background_frame assignment if only this route writes to it
    # and CameraThread only reads from it.
    print("Capturing background... Stand still.")
    
    # Brief pause to allow user to prepare, and for camera thread to provide a fresh raw frame
    time.sleep(1) # Shorter sleep as continuous capture is happening
    
    raw_frame_copy = camera_thread.get_raw_frame()

    if raw_frame_copy is not None:
        background_frame = raw_frame_copy
        print("Background captured successfully.")
        return jsonify({"status": "success", "message": "Background captured"}), 200
    else:
        print("Error: Could not get raw frame for background capture.")
        # background_frame = None # Not strictly necessary if it was already None
        return jsonify({"status": "error", "message": "Failed to capture background (no raw frame)"}), 500

def generate_video_stream():
    global camera_thread, is_camera_active
    no_signal_frame = None # Placeholder for no signal

    while True: # Loop indefinitely, actual control is is_camera_active and thread state
        if not is_camera_active or camera_thread is None or not camera_thread.is_alive():
            print("Video stream: Camera not active or thread stopped.")
            # Create a placeholder image indicating camera is off
            if no_signal_frame is None:
                img = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(img, "Camera Off", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                _,jpeg = cv2.imencode('.jpg', img)
                no_signal_frame = jpeg.tobytes()
            
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + no_signal_frame + b'\r\n')
            time.sleep(1) # Don't busy-loop if camera is off
            continue

        jpeg_frame_bytes = camera_thread.get_jpeg_frame()
        if jpeg_frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_frame_bytes + b'\r\n')
        else:
            # Could yield a "loading" frame or just wait briefly
            time.sleep(0.05) # Wait for a frame to become available

@app.route('/video_feed')
def video_feed_route():
    # is_camera_active check is done inside generate_video_stream
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)
