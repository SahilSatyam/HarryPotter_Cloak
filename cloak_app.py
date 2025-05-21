import cv2
import numpy as np
import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

class CloakApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Invisible Cloak FX")

        self.cap = None
        self.background_frame = None
        self.is_camera_running = False

        # Kernels and color bounds
        self.open_kernel = np.ones((10, 10), np.uint8)
        self.close_kernel = np.ones((10, 10), np.uint8)
        self.dilation_kernel = np.ones((10, 10), np.uint8)
        self.lower_bound = np.array([50, 80, 50])  # Example: Green screen, adjust as needed
        self.upper_bound = np.array([90, 255, 255]) # Example: Green screen, adjust as needed

        self._create_widgets()

    def _create_widgets(self):
        self.video_label = ttk.Label(self.root)
        self.video_label.pack()

        button_frame = ttk.Frame(self.root)
        button_frame.pack()

        self.btn_start_cam = ttk.Button(button_frame, text="Start Camera", command=self.start_camera)
        self.btn_start_cam.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_capture_bg = ttk.Button(button_frame, text="Capture Background", command=self.capture_bg_command, state=tk.DISABLED)
        self.btn_capture_bg.pack(side=tk.LEFT, padx=5, pady=5)

        self.btn_stop_cam = ttk.Button(button_frame, text="Stop Camera", command=self.stop_camera, state=tk.DISABLED)
        self.btn_stop_cam.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.btn_quit = ttk.Button(button_frame, text="Quit", command=self.quit_app)
        self.btn_quit.pack(side=tk.LEFT, padx=5, pady=5)

    def init_camera(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        # Check if the camera opened successfully
        if self.cap is None or not self.cap.isOpened():
            print("Error: Could not open video device.")
            messagebox.showerror("Camera Error", "Failed to open camera. Check connection/permissions.")
            self.cap = None 
        return self.cap


    def capture_background(self):
        if self.cap and self.cap.isOpened():
            time.sleep(2) # Give camera time to adjust
            ret, background = self.cap.read()
            if ret:
                self.background_frame = background
                print("Background captured.")
                # Potentially enable/disable buttons here
            else:
                print("Error: Could not capture background.")
                self.background_frame = None
        else:
            print("Error: Camera not started for background capture.")


    def filter_mask(self, mask): # Kernels are now instance variables
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.open_kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, self.close_kernel)
        mask = cv2.dilate(mask, self.dilation_kernel, iterations=1)
        return mask

    def process_frame(self, frame): # cap, background, bounds, kernels are instance variables
        if self.background_frame is None:
            # Optionally, display a message on the frame
            cv2.putText(frame, "Capture Background First!", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
            return frame
        
        # Get frame dimensions for text placement
        (h, w) = frame.shape[:2]
        
        if self.background_frame is None:
            text = "Capture Background First!"
            font_face = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1
            thickness = 2
            text_size, _ = cv2.getTextSize(text, font_face, font_scale, thickness)
            text_x = int((w - text_size[0]) / 2)
            text_y = int((h + text_size[1]) / 2)
            cv2.putText(frame, text, (text_x, text_y), 
                        font_face, font_scale, (0, 0, 255), thickness, cv2.LINE_AA)
            return frame

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower_bound, self.upper_bound)
        mask = self.filter_mask(mask)

        cloak_part = cv2.bitwise_and(frame, frame, mask=cv2.bitwise_not(mask))
        background_part = cv2.bitwise_and(self.background_frame, self.background_frame, mask=mask)
        
        combined_frame = cv2.addWeighted(cloak_part, 1, background_part, 1, 0)
        return combined_frame

    def release_resources(self):
        print("Releasing resources...")
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.is_camera_running = False
        # cv2.destroyAllWindows() # Not strictly needed if not using cv2.imshow

    def start_camera(self):
        print("Starting camera...")
        if not self.init_camera() or self.cap is None: # Check if init_camera failed or cap is None
            self.is_camera_running = False
            self.btn_start_cam.config(state=tk.NORMAL)
            self.btn_capture_bg.config(state=tk.DISABLED)
            self.btn_stop_cam.config(state=tk.DISABLED)
            return # Do not proceed to start video loop

        self.is_camera_running = True
        self.btn_start_cam.config(state=tk.DISABLED)
        self.btn_stop_cam.config(state=tk.NORMAL)
        
        if self.background_frame is None:
            self.btn_capture_bg.config(state=tk.NORMAL)
        else:
            self.btn_capture_bg.config(state=tk.DISABLED)
        self._video_loop() # Start the video loop

    def capture_bg_command(self):
        print("Preparing to capture background...")
        messagebox.showinfo("Instruction", "Prepare to capture background. Remove the 'cloak' from view and click OK.")
        
        # User clicked OK, proceed with capture
        self.capture_background() # This method already has a time.sleep()
        
        if self.background_frame is not None:
            self.btn_capture_bg.config(state=tk.DISABLED) 
            messagebox.showinfo("Success", "Background captured!")
            print("Background captured. 'Capture Background' button disabled.")
        else:
            # This case implies capture_background itself failed (e.g., camera error during capture)
            messagebox.showerror("Error", "Failed to capture background. Camera might have been disconnected.")
            # Keep the button enabled to allow another try if the camera is still running
            if self.is_camera_running:
                 self.btn_capture_bg.config(state=tk.NORMAL)
            else:
                 self.btn_capture_bg.config(state=tk.DISABLED)


    def stop_camera(self):
        print("Stopping camera...")
        self.is_camera_running = False # Signal video loop to stop
        
        # Clear the video label
        # You might want to display a static image or just clear it
        if hasattr(self.video_label, 'imgtk'):
            self.video_label.configure(image='') 
            self.video_label.image = None # Clear reference

        # The _video_loop will call release_resources when is_camera_running is false
        # if self.cap: # Ensure release is called here if stopping without quitting
        #      self.release_resources() # This might be redundant if _video_loop handles it

        self.btn_start_cam.config(state=tk.NORMAL)
        self.btn_capture_bg.config(state=tk.DISABLED)
        self.btn_stop_cam.config(state=tk.DISABLED)


    def _video_loop(self):
        if self.is_camera_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                processed_frame = self.process_frame(frame) # Pass the frame
                img = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk # Keep a reference!
                self.video_label.configure(image=imgtk)
            else:
                print("Error: Could not read frame in video loop.")
                # Optionally handle this, e.g., by stopping the loop or showing a default image
                self.is_camera_running = False # Stop loop on read error
            
            # Schedule the next frame only if still running
            if self.is_camera_running:
                self.root.after(15, self._video_loop) # Approx 66 FPS
        else:
            # If loop is stopped (e.g. by stop_camera, quit_app, or error in loop), ensure resources are released
            if self.cap is not None: # Check if cap was initialized
                 self.release_resources()


    def quit_app(self):
        print("Quitting application...")
        if self.is_camera_running:
            self.is_camera_running = False # Stop video loop
            # Video loop will call release_resources
        elif self.cap: # If camera was initialized but loop not running (e.g. error)
            self.release_resources()
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CloakApp(root)
    root.mainloop()
