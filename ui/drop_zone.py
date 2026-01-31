"""
Drop zone widget for drag and drop file import
"""
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent


class DropZone(QWidget):
    files_dropped = Signal(list)  # List of file paths
    
    def __init__(self):
        super().__init__()
        
        self.setAcceptDrops(True)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI for the drop zone"""
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        self.label = QLabel("Drag & Drop Live Photos here\nor click to select folder")
        self.label.setAlignment(Qt.AlignCenter)
        
        # Style the label
        self.label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaa;
                border-radius: 10px;
                padding: 20px;
                font-size: 16px;
                color: #777;
            }
        """)
        
        layout.addWidget(self.label)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragMoveEvent(self, event: QDragMoveEvent):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            file_paths = []
            for url in event.mimeData().urls():
                file_paths.append(url.toLocalFile())
            
            self.files_dropped.emit(file_paths)
            event.acceptProposedAction()
    
    def mousePressEvent(self, event):
        """Handle mouse click to trigger file dialog"""
        # This would normally open a file dialog, but since we're handling
        # imports through the main window's import functionality, we'll just
        # keep this as a visual element
        super().mousePressEvent(event)