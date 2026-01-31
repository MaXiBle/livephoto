"""
Module for exporting Live Photos back to files
Copies original files to export directory for transfer to iPhone
"""
import os
import shutil
from pathlib import Path
from typing import List
import sqlite3


class Exporter:
    def __init__(self, library_path: str, db_path: str, export_path: str):
        self.library_path = Path(library_path)
        self.db_path = Path(db_path)
        self.export_path = Path(export_path)
        self.export_path.mkdir(parents=True, exist_ok=True)
    
    def export_photos(self, photo_ids: List[int]) -> bool:
        """
        Export selected photos to the export directory
        Copies both image and video files if they exist
        """
        try:
            # Get photo information from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            placeholders = ','.join(['?' for _ in photo_ids])
            cursor.execute(f'''
                SELECT id, filename, filepath, video_filename FROM photos WHERE id IN ({placeholders})
            ''', photo_ids)
            
            rows = cursor.fetchall()
            conn.close()
            
            exported_count = 0
            for row in rows:
                photo_id, filename, filepath, video_filename = row
                
                # Copy image file
                src_image_path = Path(filepath)
                dst_image_path = self.export_path / filename
                
                if src_image_path.exists():
                    shutil.copy2(src_image_path, dst_image_path)
                
                # Copy video file if it exists
                if video_filename:
                    src_video_path = src_image_path.parent / video_filename
                    dst_video_path = self.export_path / video_filename
                    
                    if src_video_path.exists():
                        shutil.copy2(src_video_path, dst_video_path)
                
                exported_count += 1
            
            return True
        except Exception as e:
            print(f"Error exporting photos: {e}")
            return False
    
    def get_export_directory(self) -> str:
        """
        Get the path to the export directory
        """
        return str(self.export_path)
    
    def clear_export_directory(self):
        """
        Clear all files from the export directory
        """
        for item in self.export_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)