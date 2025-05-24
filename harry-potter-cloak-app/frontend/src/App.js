import React, { useState } from 'react';
import './App.css';

const BACKEND_URL = 'http://localhost:5000';

function App() {
  const [statusMessage, setStatusMessage] = useState('Welcome! Click "Start Camera" to begin.');
  const [statusType, setStatusType] = useState('info'); // 'info', 'success', 'error'
  const [videoFeedSrc, setVideoFeedSrc] = useState('');
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const updateStatus = (message, type) => {
    setStatusMessage(message);
    setStatusType(type);
  };

  const handleStartCamera = async () => {
    updateStatus('Starting camera...', 'info');
    setIsLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/start_camera`, { method: 'POST' });
      const data = await response.json();
      if (response.ok && data.status === 'success') {
        updateStatus(data.message || 'Camera started. Video feed should be active.', 'success');
        setVideoFeedSrc(`${BACKEND_URL}/video_feed?t=${new Date().getTime()}`);
        setIsCameraActive(true);
      } else {
        updateStatus(data.message || `Error starting camera (HTTP ${response.status})`, 'error');
        setVideoFeedSrc('');
        setIsCameraActive(false);
      }
    } catch (error) {
      console.error('Start camera error:', error);
      updateStatus(`Request failed: ${error.message}`, 'error');
      setVideoFeedSrc('');
      setIsCameraActive(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCaptureBackground = async () => {
    if (!isCameraActive) {
      updateStatus('Camera is not active. Please start the camera first.', 'error');
      return;
    }
    updateStatus('Capturing background...', 'info');
    setIsLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/capture_background`, { method: 'POST' });
      const data = await response.json();
      if (response.ok && data.status === 'success') {
        updateStatus(data.message || 'Background captured successfully!', 'success');
      } else {
        updateStatus(data.message || `Error capturing background (HTTP ${response.status})`, 'error');
      }
    } catch (error) {
      console.error('Capture background error:', error);
      updateStatus(`Request failed: ${error.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopCamera = async () => {
    updateStatus('Stopping camera...', 'info');
    setIsLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/stop_camera`, { method: 'POST' });
      const data = await response.json();
      if (response.ok && data.status === 'success') {
        updateStatus(data.message || 'Camera stopped.', 'success');
        setVideoFeedSrc('');
        setIsCameraActive(false);
      } else {
        // Use backend message if available, otherwise provide a generic one
        updateStatus(data.message || `Error stopping camera (HTTP ${response.status})`, 'error');
        // Even if stop command fails, frontend state should reflect camera as off if backend is unclear
        // setVideoFeedSrc(''); // Already done if error occurs on backend response
        // setIsCameraActive(false); // Could be risky if backend is still running camera
      }
    } catch (error) {
      console.error('Stop camera error:', error);
      updateStatus(`Request failed: ${error.message}`, 'error');
      setVideoFeedSrc(''); // Clear feed on client-side error too
      setIsCameraActive(false); // Assume camera is off if frontend request fails badly
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Harry Potter Invisibility Cloak</h1>
        <div className="video-container">
          {isCameraActive && videoFeedSrc ? (
            <img src={videoFeedSrc} alt="Video Feed" />
          ) : (
            <div className="video-placeholder">Camera is Off</div>
          )}
        </div>
        <div className="controls">
          <button onClick={handleStartCamera} disabled={isLoading || isCameraActive}>Start Camera</button>
          <button onClick={handleCaptureBackground} disabled={isLoading || !isCameraActive}>Capture Background</button>
          <button onClick={handleStopCamera} disabled={isLoading || !isCameraActive}>Stop Camera</button>
        </div>
        <p className={`status-message ${statusType}`}>{statusMessage}</p>
      </header>
    </div>
  );
}

export default App;
