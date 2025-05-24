# Harry Potter Invisibility Cloak App

## Overview

This application simulates the magical Invisibility Cloak from Harry Potter using computer vision techniques. It features a React-based frontend that communicates with a Flask backend. The backend uses OpenCV to process video from a webcam and apply the "invisibility" effect to a designated color (typically a blue or green cloth). The user interface is styled with a Harry Potter theme.

## Features

*   **Real-time Invisibility Cloak Effect:** Uses OpenCV to make a specific colored object appear invisible in a live video feed.
*   **Web-Based Interface:** User-friendly interface built with React for controlling the application.
*   **Flask Backend:** Handles video processing and streaming.
*   **Harry Potter Theming:** The frontend is styled with fonts and colors inspired by the Harry Potter universe.
*   **User Controls:** Buttons to start/stop the camera and capture the background scene.
*   **Status Feedback:** Provides users with messages about the application's state (e.g., camera started, background captured, errors).

## Project Structure

The project is organized into two main directories:

*   `frontend/`: Contains the React application for the user interface.
*   `backend/`: Contains the Flask application for video processing, API endpoints, and video streaming.

## Setup and Installation

### Prerequisites

*   Python 3.7+
*   Node.js and npm (for the frontend)
*   A webcam connected to your computer.
*   A piece of cloth of a distinct color (e.g., bright blue or green) to act as the "invisibility cloak".

### Backend Setup

1.  **Navigate to the backend directory:**
    ```bash
    cd harry-potter-cloak-app/backend
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    The required Python libraries are listed in `requirements.txt`. Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the Flask backend server:**
    ```bash
    python3 app.py
    ```
    The backend server will typically start on `http://localhost:5000`. You should see log messages indicating the server is running.

### Frontend Setup

1.  **Navigate to the frontend directory:**
    Open a new terminal window/tab for this.
    ```bash
    cd harry-potter-cloak-app/frontend
    ```

2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

3.  **Run the React frontend development server:**
    ```bash
    npm start
    ```
    This will usually open the application in your default web browser at `http://localhost:3000`.

## How to Use

1.  **Start the Application:** Ensure both the backend Flask server and the frontend React development server are running. Open the application in your browser (usually `http://localhost:3000`).

2.  **Start Camera:** Click the "Start Camera" button. Your webcam feed should appear on the screen.
    *   _Note:_ You might need to grant camera permissions to your browser.

3.  **Capture Background:**
    *   Remove the "invisibility cloak" (your colored cloth) completely from the camera's view.
    *   Click the "Capture Background" button. The application will take a snapshot of the current scene. This scene will be used to "fill in" where the cloak appears.
    *   You should see a status message confirming the background has been captured.

4.  **Use the Invisibility Cloak:**
    *   Hold up your colored cloth in front of the camera.
    *   The area covered by the cloth should now appear "invisible," showing the captured background scene instead.

5.  **Stop Camera:** Click the "Stop Camera" button to turn off the webcam feed and end the effect.

## API Endpoints (Backend)

The Flask backend provides the following API endpoints (running on `http://localhost:5000`):

*   **`POST /start_camera`**: Initializes and starts the camera.
    *   *Success Response (200)*: `{"status": "success", "message": "Camera started"}` or `{"status": "success", "message": "Camera already running"}`
    *   *Error Response (500)*: `{"status": "error", "message": "Failed to open camera within thread"}`
*   **`POST /stop_camera`**: Stops the camera and releases resources.
    *   *Success Response (200)*: `{"status": "success", "message": "Camera stopped and resources released"}` or `{"status": "success", "message": "Camera already stopped"}`
    *   *Error Response (500)*: `{"status": "error", "message": "Camera thread did not stop cleanly..."}`
*   **`POST /capture_background`**: Captures the current frame from the camera to be used as the background for the invisibility effect.
    *   *Success Response (200)*: `{"status": "success", "message": "Background captured"}`
    *   *Error Response (400)*: `{"status": "error", "message": "Camera not running or not initialized..."}`
    *   *Error Response (500)*: `{"status": "error", "message": "Failed to capture background (no raw frame)"}`
*   **`GET /video_feed`**: Provides a multipart JPEG stream of the processed video (or placeholder images like "Camera Off" / "BG Not Captured").

---
Enjoy your magical Invisibility Cloak experience!
