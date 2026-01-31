"""
Preview widget for displaying Live Photos with animation capability
Shows thumbnail with wave icon for Live Photos
"""
import os
from pathlib import Path

from PySide6.QtWidgets import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, 
                               QFrame, QCheckBox)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen

from core.playback import LivePhotoPreview


class PreviewWidget(QFrame):
    photo_selected = Signal(int, bool)  # photo_id, selected
    photo_double_clicked = Signal(int)  # photo_id
    
    def __init__(self, photo_id: int, image_path: str, has_video: bool, timestamp: str):
        super().__init__()
        
        self.photo_id = photo_id
        self.image_path = image_path
        self.has_video = has_video
        self.timestamp = timestamp
        
        # Animation related attributes
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation_frame)
        self.is_hovered = False
        self.is_selected = False
        self.animation_counter = 0
        self.max_animation_frames = 90  # At 30fps, this is 3 seconds
        
        # Live photo preview object
        self.live_preview = LivePhotoPreview()
        
        # Set up the UI
        self.setup_ui()
        
        # Load the live photo if it has video
        if self.has_video:
            # Find the corresponding video file
            video_path = self.find_video_path()
            success = self.live_preview.load_live_photo(self.image_path, video_path)
            if not success:
                self.has_video = False  # Fallback to static image
        
        # Set up event handling
        self.setMouseTracking(True)
        self.installEventFilter(self)
        
        # Style the frame
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(2)
        self.update_style()
    
    def setup_ui(self):
        """Setup the UI elements for the preview widget"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Thumbnail label
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        
        # Set fixed size for consistent grid layout
        self.thumbnail_label.setFixedSize(160, 160)
        self.thumbnail_label.setMinimumSize(160, 160)
        
        # Create initial thumbnail
        self.create_thumbnail()
        
        # Overlay for wave icon if it's a live photo
        self.overlay_label = QLabel()
        self.overlay_label.setParent(self.thumbnail_label)
        self.overlay_label.setGeometry(160 - 24, 160 - 24, 20, 20)  # Bottom right corner
        
        if self.has_video:
            # Draw a simple wave icon to indicate Live Photo
            pixmap = self.create_wave_icon()
            self.overlay_label.setPixmap(pixmap)
            self.overlay_label.show()
        else:
            self.overlay_label.hide()
        
        layout.addWidget(self.thumbnail_label)
    
    def create_thumbnail(self):
        """Create thumbnail from image file"""
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                # Scale the image to fit within 160x160 while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    160, 160, 
                    Qt.KeepAspectRatio, 
                    Qt.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(scaled_pixmap)
            else:
                # Fallback: create a placeholder
                pixmap = self.create_placeholder_pixmap()
                self.thumbnail_label.setPixmap(pixmap)
        else:
            # Fallback: create a placeholder
            pixmap = self.create_placeholder_pixmap()
            self.thumbnail_label.setPixmap(pixmap)
    
    def create_placeholder_pixmap(self) -> QPixmap:
        """Create a placeholder pixmap when image can't be loaded"""
        pixmap = QPixmap(160, 160)
        pixmap.fill(QColor(240, 240, 240))  # Light gray background
        
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        painter.drawRect(0, 0, 159, 159)
        
        painter.setFont(QFont("Arial", 10))
        painter.setPen(QColor(150, 150, 150))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "No Image")
        painter.end()
        
        return pixmap
    
    def create_wave_icon(self) -> QPixmap:
        """Create a small wave icon to indicate Live Photo"""
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw a simple wave pattern
        pen = QPen(QColor(0, 150, 255), 2)
        painter.setPen(pen)
        
        # Draw wave shape
        points = [
            (2, 10),
            (6, 6),
            (10, 10),
            (14, 6),
            (18, 10)
        ]
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        painter.end()
        return pixmap
    
    def find_video_path(self) -> str:
        """Find the corresponding video file for this Live Photo"""
        image_path_obj = Path(self.image_path)
        base_name = image_path_obj.stem  # Filename without extension
        
        # Look for corresponding .MOV file in the same directory
        video_candidates = [
            image_path_obj.parent / f"{base_name}.MOV",
            image_path_obj.parent / f"{base_name}.mov",
        ]
        
        for candidate in video_candidates:
            if candidate.exists():
                return str(candidate)
        
        # If no MOV file found, return None
        return None
    
    def enterEvent(self, event):
        """Handle mouse entering the widget"""
        self.is_hovered = True
        if self.has_video:
            # Start animation after a short delay (to simulate the 400ms mentioned in spec)
            QTimer.singleShot(400, self.start_animation_if_hovered)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leaving the widget"""
        self.is_hovered = False
        if self.animation_timer.isActive():
            self.animation_timer.stop()
            self.create_thumbnail()  # Revert to static image
        super().leaveEvent(event)
    
    def start_animation_if_hovered(self):
        """Start animation if still hovered after delay"""
        if self.is_hovered and self.has_video:
            self.animation_counter = 0
            self.animation_timer.start(33)  # ~30 FPS
    
    def update_animation_frame(self):
        """Update the animation frame"""
        if not self.is_hovered:
            self.animation_timer.stop()
            self.create_thumbnail()
            return
        
        if self.has_video and self.live_preview.is_loaded:
            frame = self.live_preview.get_video_frame(160, 160)
            if frame is not None:
                # Convert OpenCV BGR to RGB
                height, width, channel = frame.shape
                bytes_per_line = 3 * width
                qt_image = self.convert_opencv_to_qpixmap(frame)
                self.thumbnail_label.setPixmap(qt_image)
        
        self.animation_counter += 1
        
        # Stop after max frames (about 3 seconds at 30fps)
        if self.animation_counter >= self.max_animation_frames:
            self.animation_timer.stop()
            self.create_thumbnail()  # Return to static image
    
    def convert_opencv_to_qpixmap(self, cv_image) -> QPixmap:
        """Convert OpenCV image to QPixmap"""
        from PySide6.QtGui import QImage
        # Convert BGR to RGB
        rgb_image = cv_image[:, :, ::-1].copy()
        
        height, width, channel = rgb_image.shape
        bytes_per_line = channel * width
        q_img = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        return QPixmap.fromImage(q_img)
    
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if event.button() == Qt.LeftButton:
            self.is_selected = not self.is_selected
            self.update_style()
            self.photo_selected.emit(self.photo_id, self.is_selected)
        super().mousePressEvent(event)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double click events"""
        if event.button() == Qt.LeftButton:
            self.photo_double_clicked.emit(self.photo_id)
        super().mouseDoubleClickEvent(event)
    
    def update_style(self):
        """Update the visual style based on selection state"""
        if self.is_selected:
            self.setStyleSheet("QFrame { border: 2px solid #0078D4; }")
        else:
            self.setStyleSheet("QFrame { border: 2px solid transparent; }")
    
    def sizeHint(self):
        """Return preferred size for the widget"""
        return QSize(170, 170)  # Slightly larger than the thumbnail to account for borders
    
    def minimumSizeHint(self):
        """Return minimum size for the widget"""
        return QSize(170, 170)
    
    def cleanup(self):
        """Clean up resources when widget is destroyed"""
        if self.animation_timer:
            self.animation_timer.stop()
        if self.live_preview:
            self.live_preview.release()