"""
Module for playing back Live Photos
Handles video overlay animation on top of static image
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import threading
import time


class LivePhotoPlayer:
    def __init__(self):
        self.current_video_cap = None
        self.video_thread = None
        self.is_playing = False
        self.should_stop = False
    
    def load_video(self, video_path: str) -> bool:
        """
        Load video file for playback
        """
        try:
            if self.current_video_cap:
                self.current_video_cap.release()
            
            self.current_video_cap = cv2.VideoCapture(video_path)
            if not self.current_video_cap.isOpened():
                return False
            
            # Get video properties
            self.fps = self.current_video_cap.get(cv2.CAP_PROP_FPS)
            self.frame_count = int(self.current_video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.duration = self.frame_count / self.fps if self.fps > 0 else 0
            
            return True
        except Exception:
            return False
    
    def play_video_frame(self) -> Optional[np.ndarray]:
        """
        Get the next frame from the video
        """
        if not self.current_video_cap or not self.current_video_cap.isOpened():
            return None
        
        ret, frame = self.current_video_cap.read()
        if not ret:
            # Loop back to beginning if we reached the end
            self.current_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.current_video_cap.read()
            if not ret:
                return None
        
        return frame
    
    def reset_video_position(self):
        """
        Reset video to the beginning
        """
        if self.current_video_cap:
            self.current_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    def release(self):
        """
        Release video resources
        """
        if self.current_video_cap:
            self.current_video_cap.release()
            self.current_video_cap = None


class LivePhotoPreview:
    def __init__(self):
        self.player = LivePhotoPlayer()
        self.image_path = None
        self.video_path = None
        self.is_loaded = False
    
    def load_live_photo(self, image_path: str, video_path: Optional[str] = None) -> bool:
        """
        Load a Live Photo (image + optional video)
        """
        self.image_path = image_path
        self.video_path = video_path
        
        # Load static image
        try:
            self.static_image = cv2.imread(image_path)
            if self.static_image is None:
                return False
        except Exception:
            return False
        
        # Load video if provided
        if video_path and Path(video_path).exists():
            success = self.player.load_video(video_path)
            if not success:
                self.video_path = None
                self.player = LivePhotoPlayer()  # Reset player
                return False
        
        self.is_loaded = True
        return True
    
    def get_static_preview(self, width: int = 160, height: int = 160) -> np.ndarray:
        """
        Get the static image preview (resized)
        """
        if not self.is_loaded:
            raise ValueError("Live Photo not loaded")
        
        # Resize the image maintaining aspect ratio
        h, w = self.static_image.shape[:2]
        
        # Calculate scaling factor to fit within the desired dimensions
        scale_w = width / w
        scale_h = height / h
        scale = min(scale_w, scale_h)
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized = cv2.resize(self.static_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Create a canvas of the target size with black background
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Center the resized image on the canvas
        y_offset = (height - new_h) // 2
        x_offset = (width - new_w) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return canvas
    
    def get_video_frame(self, width: int = 160, height: int = 160) -> Optional[np.ndarray]:
        """
        Get the next video frame (resized to match static image)
        """
        if not self.video_path or not self.is_loaded:
            return self.get_static_preview(width, height)
        
        frame = self.player.play_video_frame()
        if frame is None:
            return self.get_static_preview(width, height)
        
        # Resize the video frame to match the static image size
        h, w = frame.shape[:2]
        
        # Calculate scaling factor to fit within the desired dimensions
        scale_w = width / w
        scale_h = height / h
        scale = min(scale_w, scale_h)
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # Create a canvas of the target size with black background
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Center the resized frame on the canvas
        y_offset = (height - new_h) // 2
        x_offset = (width - new_w) // 2
        canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
        
        return canvas
    
    def start_animation(self, callback, duration: float = 3.0):
        """
        Start playing the Live Photo animation for a specified duration
        """
        if not self.video_path:
            # If no video, just call the callback with static image
            callback(self.get_static_preview())
            return
        
        start_time = time.time()
        while time.time() - start_time < duration and self.is_loaded:
            frame = self.get_video_frame()
            if frame is not None:
                callback(frame)
            
            # Small delay to control frame rate
            time.sleep(1.0/30)  # ~30 FPS
        
        # Reset video position when done
        self.player.reset_video_position()
    
    def stop_animation(self):
        """
        Stop the current animation
        """
        pass  # Animation runs in main thread, no stopping needed
    
    def release(self):
        """
        Release all resources
        """
        self.player.release()
        self.is_loaded = False