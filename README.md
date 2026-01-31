# LiveVault - Live Photo Manager

LiveVault is a desktop application for managing Live Photos from iPhone. It allows you to import, store, view, and export Live Photos while preserving their original format.

## Features

- Import Live Photos from iPhone (both single HEIC files with embedded video and HEIC+MOV pairs)
- Organized storage with automatic folder structure by date
- Animated preview of Live Photos on hover
- Batch export to transfer photos back to iPhone
- Search and filtering capabilities
- Statistics about your collection

## Requirements

- Python 3.10+
- Windows 10/11 (64-bit)

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```
   python main.py
   ```

2. To import Live Photos:
   - Connect your iPhone and copy the DCIM folder to your computer
   - Click "Import" or drag and drop the folder onto the drop zone
   - The app will automatically detect Live Photos and organize them

3. To view Live Photos:
   - Hover over a thumbnail to see the animated preview
   - Double-click to view in fullscreen

4. To export Live Photos:
   - Select the photos you want to export
   - Click "Export" to copy the original files to Documents\LiveVault\Export
   - Transfer these files back to your iPhone using one of the methods described in the app

## How to Transfer Photos Back to iPhone

After exporting, you can transfer the files back to your iPhone using one of these methods:

1. **USB**: Copy files to iPhone's DCIM folder (requires iTunes/Finder)
2. **WALTR 2 (free)**: Drag files into the WALTR application
3. **Email**: Attach .HEIC files to an email and save them on your iPhone

Note: iPhone may show only the photo without animation. This is a limitation of Apple's ecosystem.

## Technical Details

- The application stores files in `%APPDATA%\LiveVault\library\` organized by year/month
- A SQLite database tracks all photos and their metadata
- Original files are preserved without modification
- Video previews are generated without extracting files to temporary locations