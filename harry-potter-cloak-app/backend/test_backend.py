import subprocess
import time
import requests
import os
import signal
import sys

# Configuration
BASE_URL = "http://127.0.0.1:5000"
APP_PATH = "app.py" # Relative to APP_DIR
APP_DIR = os.path.dirname(os.path.abspath(__file__)) # Script's own directory
PYTHON_EXE = sys.executable # Use the same python that runs the script

flask_process = None
tests_passed = True # Track overall test status

def print_flush(*args, **kwargs):
    print(*args, **kwargs)
    sys.stdout.flush()

def start_flask_app():
    global flask_process
    print_flush(f"Starting Flask app: {APP_PATH} in {APP_DIR}")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1" # Ensure subprocess output is not buffered

    # Try to find flask in local user install path if system python doesn't have it
    local_bin_path = os.path.expanduser("~/.local/bin")
    if local_bin_path not in env["PATH"]:
        env["PATH"] = f"{local_bin_path}:{env['PATH']}"

    flask_process = subprocess.Popen(
        [PYTHON_EXE, APP_PATH], 
        cwd=APP_DIR, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid, # Make it a session leader
        env=env
    )
    time.sleep(4) # Reduced sleep
    print_flush(f"Flask app hopefully started. Process ID: {flask_process.pid if flask_process else 'N/A'}")
    if flask_process is None or flask_process.poll() is not None:
        print_flush("Flask process did not start or exited prematurely!")
        if flask_process:
            stdout, stderr = flask_process.communicate()
            print_flush(f"Flask App STDOUT (on failure): {stdout.decode(errors='ignore')}")
            print_flush(f"Flask App STDERR (on failure): {stderr.decode(errors='ignore')}")
        raise RuntimeError("Flask app failed to start.")


def stop_flask_app():
    global flask_process
    if flask_process and flask_process.poll() is None:
        print_flush(f"Stopping Flask app (PID: {flask_process.pid})...")
        try:
            os.killpg(os.getpgid(flask_process.pid), signal.SIGINT)
            stdout, stderr = flask_process.communicate(timeout=7) # Reduced timeout slightly
            print_flush("Flask app process terminated.")
            print_flush(f"APP_STDOUT: {stdout.decode(errors='ignore').strip()}")
            print_flush(f"APP_STDERR: {stderr.decode(errors='ignore').strip()}")
        except subprocess.TimeoutExpired:
            print_flush("Flask app did not terminate gracefully, killing.")
            os.killpg(os.getpgid(flask_process.pid), signal.SIGKILL)
            stdout, stderr = flask_process.communicate()
            print_flush("Flask app process killed.")
            print_flush(f"APP_STDOUT (on kill): {stdout.decode(errors='ignore').strip()}")
            print_flush(f"APP_STDERR (on kill): {stderr.decode(errors='ignore').strip()}")
        except Exception as e:
            print_flush(f"Error stopping Flask app: {e}")
    elif flask_process:
        print_flush("Flask app was already terminated or failed to run.")
        stdout, stderr = flask_process.communicate()
        print_flush(f"APP_STDOUT (already stopped): {stdout.decode(errors='ignore').strip()}")
        print_flush(f"APP_STDERR (already stopped): {stderr.decode(errors='ignore').strip()}")
    else:
        print_flush("Flask app was not started or already cleaned up.")
    flask_process = None


def run_test(name, method, endpoint, expected_status_codes, expected_json_contains=None, headers=None, json_payload=None, stream_check=False):
    global tests_passed
    print_flush(f"\n--- Test: {name} ---")
    url = f"{BASE_URL}{endpoint}"
    try:
        # For stream checks, we might only want headers, or a very short read.
        # For non-stream, timeout can be shorter.
        request_timeout = 5 if stream_check else 10
        
        response = requests.request(method, url, headers=headers, json=json_payload, timeout=request_timeout, stream=stream_check)
        print_flush(f"Status Code: {response.status_code}")
        
        content_type = response.headers.get("Content-Type", "")
        print_flush(f"Content-Type: {content_type}")

        if not (response.status_code in expected_status_codes):
            tests_passed = False
            print_flush(f"ERROR: Expected status {expected_status_codes}, got {response.status_code}")

        if "application/json" in content_type:
            response_json = response.json()
            print_flush(f"Response JSON: {response_json}")
            if expected_json_contains:
                for key, value in expected_json_contains.items():
                    if response_json.get(key) != value:
                        tests_passed = False
                        print_flush(f"ERROR: Expected JSON key '{key}' to be '{value}', got '{response_json.get(key)}'")
        elif stream_check and "multipart/x-mixed-replace" in content_type:
            print_flush("Response is a stream (multipart/x-mixed-replace). Checked headers.")
            # Simplified: Don't try to read content for now due to environment limits
            if not response.headers.get("Content-Type", "").startswith("multipart/x-mixed-replace"):
                tests_passed = False
                print_flush("ERROR: Stream test expected multipart/x-mixed-replace Content-Type.")
            response.close() # Close the stream connection
        elif not stream_check:
             print_flush(f"Response Text (first 200 chars): {response.text[:200]}")


        print_flush(f"Test '{name}' COMPLETED.")
        return response
    except requests.exceptions.Timeout:
        tests_passed = False
        print_flush(f"Test '{name}' FAILED with requests.exceptions.Timeout (timeout was {request_timeout}s)")
        return None
    except Exception as e:
        tests_passed = False
        print_flush(f"Test '{name}' FAILED with exception: {e}")
        return None

def main_tests():
    run_test("Start Camera (Expect Device Error)", "POST", "/start_camera", [500], {"status": "error", "message": "Failed to open camera within thread"})
    run_test("Start Camera Again (Expect Device Error)", "POST", "/start_camera", [500], {"status": "error", "message": "Failed to open camera within thread"})
    run_test("Capture Background (Camera Not Active)", "POST", "/capture_background", [400], {"status": "error", "message": "Camera not running or not initialized. Start camera first."})
    
    video_feed_resp = run_test("Video Feed (Camera Not Active)", "GET", "/video_feed", [200], stream_check=True)
    if video_feed_resp and not ("multipart/x-mixed-replace" in video_feed_resp.headers.get("Content-Type", "")):
        global tests_passed # Ensure modification of global
        tests_passed = False
        print_flush("ERROR: Video feed Content-Type check failed for 'Camera Not Active' case.")

    run_test("Stop Camera (Effectively Already Stopped)", "POST", "/stop_camera", [200], {"status": "success", "message": "Camera already stopped"})
    run_test("Stop Camera Again (Still Stopped)", "POST", "/stop_camera", [200], {"status": "success", "message": "Camera already stopped"})

    print_flush("\n--- All planned tests executed ---")

if __name__ == "__main__":
    all_passed_locally = False
    try:
        print_flush("Starting test script execution...")
        start_flask_app()
        if flask_process and flask_process.poll() is None:
            print_flush("Flask process confirmed running. Proceeding with tests.")
            main_tests()
            all_passed_locally = tests_passed
        else:
            print_flush("Flask process did not start or exited prematurely. Check logs above.")
            all_passed_locally = False

    except Exception as e:
        print_flush(f"An error occurred during the test run: {e}")
        all_passed_locally = False
    finally:
        print_flush("Stopping Flask app from finally block...")
        stop_flask_app()
        if all_passed_locally:
            print_flush("RESULT: All tests passed.")
        else:
            print_flush("RESULT: Some tests FAILED.")
        print_flush("Test script finished.")
        sys.exit(0 if all_passed_locally else 1)
