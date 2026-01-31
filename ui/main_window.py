"""
Main application window for LiveVault
Displays grid of Live Photos with toolbar and status bar
"""
import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QGridLayout, QPushButton, QLabel, 
                               QStatusBar, QMenuBar, QMenu, QAction, QFileDialog,
                               QScrollArea, QMessageBox, QCalendarWidget, QLineEdit,
                               QToolBar)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QPixmap, QIcon, QKeySequence, QActionGroup

from core.importer import Importer
from core.library import LibraryManager
from core.exporter import Exporter
from ui.preview_widget import PreviewWidget
from ui.drop_zone import DropZone


class PhotoLoadingWorker(QThread):
    """
    Worker thread for loading photos to avoid blocking the UI
    """
    photos_loaded = Signal(list)
    
    def __init__(self, library_manager):
        super().__init__()
        self.library_manager = library_manager
    
    def run(self):
        photos = self.library_manager.get_all_photos()
        self.photos_loaded.emit(photos)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LiveVault - Live Photo Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize core components
        self.app_data_path = Path(os.getenv('APPDATA')) / 'LiveVault'
        self.library_path = self.app_data_path / 'library'
        self.db_path = self.app_data_path / 'library.db'
        self.export_path = Path.home() / 'Documents' / 'LiveVault' / 'Export'
        
        self.library_manager = LibraryManager(str(self.library_path), str(self.db_path))
        self.importer = Importer(str(self.library_path), str(self.db_path))
        self.exporter = Exporter(str(self.library_path), str(self.db_path), str(self.export_path))
        
        # Create necessary directories
        self.library_path.mkdir(parents=True, exist_ok=True)
        self.export_path.mkdir(parents=True, exist_ok=True)
        
        # Selected photos for batch operations
        self.selected_photos = []
        
        # Setup UI
        self.setup_ui()
        self.load_photos()
        
        # Show first-time instruction if needed
        self.show_first_time_instruction()
    
    def setup_ui(self):
        """Setup the main UI elements"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        self.setup_toolbar()
        main_layout.addWidget(self.toolbar)
        
        # Search and filter bar
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by filename...")
        self.search_input.textChanged.connect(self.on_search_changed)
        
        self.calendar_button = QPushButton("Select Date Range")
        self.calendar_button.clicked.connect(self.open_calendar_dialog)
        
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.calendar_button)
        search_layout.addStretch()
        
        main_layout.addLayout(search_layout)
        
        # Drop zone area
        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.handle_dropped_files)
        main_layout.addWidget(self.drop_zone)
        
        # Scroll area for photo grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Photo grid container
        self.grid_container = QWidget()
        self.photo_grid = QGridLayout(self.grid_container)
        self.photo_grid.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status()
    
    def setup_toolbar(self):
        """Setup the toolbar with actions"""
        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        
        # Import button
        import_action = QAction("Import", self)
        import_action.setToolTip("Import Live Photos from folder")
        import_action.triggered.connect(self.import_photos)
        self.toolbar.addAction(import_action)
        
        # Export button
        export_action = QAction("Export", self)
        export_action.setToolTip("Export selected Live Photos")
        export_action.triggered.connect(self.export_selected_photos)
        self.toolbar.addAction(export_action)
        
        # Refresh button
        refresh_action = QAction("Refresh", self)
        refresh_action.setToolTip("Refresh library")
        refresh_action.triggered.connect(self.load_photos)
        self.toolbar.addAction(refresh_action)
        
        # Add stretch to push other elements to the left
        self.toolbar.addSeparator()
        self.toolbar.addWidget(QWidget(), 1)  # Add stretching widget
        
        # Stats label
        self.stats_label = QLabel()
        self.toolbar.addWidget(self.stats_label)
    
    def show_first_time_instruction(self):
        """Show instructions for transferring photos back to iPhone"""
        settings_path = self.app_data_path / 'settings.json'
        if not settings_path.exists():
            # Mark that we've shown the instructions
            settings_path.write_text('{"shown_instructions": true}')
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("How to Transfer Photos Back to iPhone")
            msg_box.setText("""
                <h3>How to Transfer Photos Back to iPhone</h3>
                <ol>
                    <li>Click "Export" for selected photos</li>
                    <li>Open folder <code>Documents\\LiveVault\\Export</code></li>
                    <li>Transfer files to iPhone using one of these methods:
                        <ul>
                            <li><strong>USB:</strong> Copy to <em>Internal Storage → DCIM</em> (requires iTunes)</li>
                            <li><strong>WALTR 2 (free):</strong> Drag files into the application</li>
                            <li><strong>Email:</strong> Attach .HEIC files to email → save on iPhone</li>
                        </ul>
                    </li>
                </ol>
                <p><strong>Note:</strong> iPhone may show only the photo without animation. This is a limitation of Apple's ecosystem.</p>
            """)
            msg_box.exec()
    
    def import_photos(self):
        """Handle importing photos via file dialog"""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder with Live Photos")
        if folder_path:
            try:
                count = self.importer.import_to_library(folder_path)
                QMessageBox.information(self, "Import Complete", f"Successfully imported {count} Live Photos!")
                self.load_photos()
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import photos: {str(e)}")
    
    def handle_dropped_files(self, file_paths):
        """Handle files dropped onto the drop zone"""
        # For simplicity, we'll treat the first directory as the source
        dirs = [f for f in file_paths if os.path.isdir(f)]
        if dirs:
            try:
                count = self.importer.import_to_library(dirs[0])
                QMessageBox.information(self, "Import Complete", f"Successfully imported {count} Live Photos!")
                self.load_photos()
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import photos: {str(e)}")
        else:
            # If only files were dropped, we could potentially support individual file import
            # For now, just show a message
            QMessageBox.information(self, "Info", "Please drop a folder containing Live Photos.")
    
    def load_photos(self):
        """Load photos from the library and display them"""
        # Clear existing widgets in the grid
        self.clear_photo_grid()
        
        # Use worker thread to load photos
        self.worker = PhotoLoadingWorker(self.library_manager)
        self.worker.photos_loaded.connect(self.display_photos)
        self.worker.start()
    
    def clear_photo_grid(self):
        """Clear all widgets from the photo grid"""
        for i in reversed(range(self.photo_grid.count())):
            widget = self.photo_grid.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)
    
    def display_photos(self, photos):
        """Display photos in the grid"""
        # Clear existing widgets
        self.clear_photo_grid()
        
        # Add photos to grid (3 per row for desktop app)
        for i, photo in enumerate(photos):
            row = i // 3
            col = i % 3
            
            # Create preview widget
            preview_widget = PreviewWidget(
                photo_id=photo['id'],
                image_path=photo['filepath'],
                has_video=bool(photo['has_video']),
                timestamp=photo['timestamp']
            )
            preview_widget.photo_selected.connect(self.on_photo_selected)
            preview_widget.photo_double_clicked.connect(self.on_photo_double_clicked)
            
            self.photo_grid.addWidget(preview_widget, row, col)
        
        # Update status
        self.update_status()
    
    def on_photo_selected(self, photo_id, selected):
        """Handle photo selection/deselection"""
        if selected:
            if photo_id not in self.selected_photos:
                self.selected_photos.append(photo_id)
        else:
            if photo_id in self.selected_photos:
                self.selected_photos.remove(photo_id)
    
    def on_photo_double_clicked(self, photo_id):
        """Handle double-click on a photo (show fullscreen)"""
        # For now, just show a message
        photo = self.library_manager.get_photo_by_id(photo_id)
        if photo:
            QMessageBox.information(self, "Fullscreen View", f"Showing {photo['filename']} in fullscreen")
    
    def on_search_changed(self, text):
        """Handle search input changes"""
        # Simple implementation - reload with search filter
        self.clear_photo_grid()
        
        # In a real implementation, we'd want to filter on the worker thread
        if text.strip():
            photos = self.library_manager.search_photos(query=text)
        else:
            photos = self.library_manager.get_all_photos()
        
        self.display_photos(photos)
    
    def open_calendar_dialog(self):
        """Open calendar dialog for date range selection"""
        # For simplicity, just show a message
        # In a real implementation, this would show a date range picker
        QMessageBox.information(self, "Date Filter", "Date range filtering coming soon!")
    
    def export_selected_photos(self):
        """Export selected photos"""
        if not self.selected_photos:
            QMessageBox.information(self, "No Selection", "Please select photos to export.")
            return
        
        try:
            success = self.exporter.export_photos(self.selected_photos)
            if success:
                QMessageBox.information(
                    self, 
                    "Export Complete", 
                    f"Exported {len(self.selected_photos)} photos to:\n{self.exporter.get_export_directory()}"
                )
            else:
                QMessageBox.critical(self, "Export Failed", "Failed to export photos.")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export photos: {str(e)}")
    
    def update_status(self):
        """Update the status bar with library statistics"""
        stats = self.library_manager.get_stats()
        status_text = f"Storage: {stats['total_size_gb']} GB | {stats['live_photos']} live photos"
        self.status_bar.showMessage(status_text)
        
        # Update toolbar stats
        self.stats_label.setText(status_text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())