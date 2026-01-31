"""
Module for importing Live Photos from iPhone
Handles both single .HEIC files with embedded video and pairs of .HEIC + .MOV files
"""
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
import pyheif
from PIL import Image
import sqlite3
from datetime import datetime


class Importer:
    def __init__(self, library_path: str, db_path: str):
        self.library_path = Path(library_path)
        self.db_path = Path(db_path)
        
    def scan_for_live_photos(self, source_path: str) -> List[dict]:
        """
        Scan source directory for Live Photo pairs or single HEIC files
        Returns list of dictionaries with photo information
        """
        source_path = Path(source_path)
        live_photos = []
        
        # Find all potential Live Photo files
        heic_files = list(source_path.rglob("*.HEIC"))
        mov_files = list(source_path.rglob("*.MOV"))
        
        # Group files by base name (without extension)
        file_groups = {}
        
        for file in heic_files + mov_files:
            # Get base name without extension (e.g., IMG_1234)
            base_name = file.stem
            if base_name.startswith('.'):
                continue
                
            if base_name not in file_groups:
                file_groups[base_name] = {'HEIC': None, 'MOV': None}
            
            if file.suffix.upper() == '.HEIC':
                file_groups[base_name]['HEIC'] = file
            elif file.suffix.upper() == '.MOV':
                file_groups[base_name]['MOV'] = file
        
        # Process each group to identify Live Photos
        for base_name, files in file_groups.items():
            if files['HEIC'] and files['MOV']:
                # This is a Live Photo pair
                live_photo_data = {
                    'type': 'pair',
                    'image_path': files['HEIC'],
                    'video_path': files['MOV'],
                    'base_name': base_name,
                    'timestamp': self._get_file_timestamp(files['HEIC'])
                }
                live_photos.append(live_photo_data)
            elif files['HEIC']:
                # Check if this HEIC has embedded video metadata
                if self._has_embedded_video(files['HEIC']):
                    live_photo_data = {
                        'type': 'single',
                        'image_path': files['HEIC'],
                        'video_path': None,  # Will be extracted during processing
                        'base_name': base_name,
                        'timestamp': self._get_file_timestamp(files['HEIC'])
                    }
                    live_photos.append(live_photo_data)
        
        return live_photos
    
    def _has_embedded_video(self, heic_path: Path) -> bool:
        """
        Check if HEIC file has embedded video (Live Photo)
        """
        try:
            # Attempt to read HEIF file to check for embedded video
            heif_file = pyheif.read(heif_file=str(heic_path))
            # Check if there are auxiliary images (which could include video)
            if hasattr(heif_file, 'aux') and heif_file.aux:
                for aux_img in heif_file.aux:
                    if aux_img.type == 'vid':
                        return True
            return False
        except Exception:
            return False
    
    def _get_file_timestamp(self, file_path: Path) -> datetime:
        """
        Get file creation/modification timestamp
        """
        stat = file_path.stat()
        return datetime.fromtimestamp(max(stat.st_ctime, stat.st_mtime))
    
    def import_to_library(self, source_path: str, callback=None) -> int:
        """
        Import Live Photos from source to library
        Calls callback with progress updates if provided
        Returns number of imported photos
        """
        live_photos = self.scan_for_live_photos(source_path)
        imported_count = 0
        
        for i, live_photo in enumerate(live_photos):
            # Create destination folder based on timestamp
            timestamp = live_photo['timestamp']
            year_month_folder = self.library_path / str(timestamp.year) / f"{timestamp.month:02d}"
            year_month_folder.mkdir(parents=True, exist_ok=True)
            
            # Copy image file
            dest_image_path = year_month_folder / live_photo['image_path'].name
            shutil.copy2(live_photo['image_path'], dest_image_path)
            
            # Handle video file if it exists
            dest_video_path = None
            if live_photo['type'] == 'pair' and live_photo['video_path']:
                dest_video_path = year_month_folder / live_photo['video_path'].name
                shutil.copy2(live_photo['video_path'], dest_video_path)
            elif live_photo['type'] == 'single':
                # Extract embedded video if present
                video_extracted = self._extract_video_from_heic(live_photo['image_path'], year_month_folder)
                if video_extracted:
                    dest_video_path = video_extracted
            
            # Add to database
            self._add_to_database(
                dest_image_path.name,
                timestamp,
                dest_video_path is not None,
                dest_video_path.name if dest_video_path else None
            )
            
            imported_count += 1
            
            # Report progress
            if callback:
                callback(i + 1, len(live_photos))
        
        return imported_count
    
    def _extract_video_from_heic(self, heic_path: Path, dest_folder: Path) -> Optional[Path]:
        """
        Extract embedded video from HEIC file and save as MOV
        """
        try:
            # This is a simplified approach - in reality, extracting embedded videos
            # from HEIC requires specific handling based on the encoding
            # For now, we'll just return None indicating no video was extracted
            # Actual implementation would depend on the specific HEIC format used by iPhone
            return None
        except Exception:
            return None
    
    def _add_to_database(self, filename: str, timestamp: datetime, has_video: bool, video_filename: str = None):
        """
        Add photo information to SQLite database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT,
                timestamp DATETIME,
                has_video BOOLEAN,
                video_filename TEXT,
                duration REAL DEFAULT 0
            )
        ''')
        
        # Insert photo record
        cursor.execute('''
            INSERT INTO photos (filename, filepath, timestamp, has_video, video_filename)
            VALUES (?, ?, ?, ?, ?)
        ''', (filename, str(self.library_path / timestamp.strftime('%Y/%m') / filename), 
              timestamp, has_video, video_filename))
        
        conn.commit()
        conn.close()