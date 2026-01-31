"""
Main entry point for LiveVault application
"""
import sys
import os
from pathlib import Path

# Add the workspace to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    # Enable high DPI scaling
    if hasattr(QApplication, 'setHighDpiScaleFactorRoundingPolicy'):
        from PySide6.QtCore import Qt
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    
    app = QApplication(sys.argv)
    app.setApplicationName("LiveVault")
    app.setApplicationVersion("1.0")
    
    # Set application icon if available
    from PySide6.QtGui import QIcon
    icon_path = Path(__file__).parent / "resources" / "icons" / "app_icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()