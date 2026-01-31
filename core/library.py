"""
Module for managing the Live Photo library
Handles database operations and file system organization
"""
import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class LibraryManager:
    def __init__(self, library_path: str, db_path: str):
        self.library_path = Path(library_path)
        self.db_path = Path(db_path)
        self.init_db()
    
    def init_db(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        
        conn.commit()
        conn.close()
    
    def get_all_photos(self, sort_by='timestamp DESC') -> List[Dict]:
        """Get all photos from the library"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f'''
            SELECT * FROM photos ORDER BY {sort_by}
        ''')
        
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        photos = []
        for row in rows:
            photo_dict = dict(zip(columns, row))
            photos.append(photo_dict)
        
        conn.close()
        return photos
    
    def search_photos(self, query: str = '', date_from: Optional[datetime] = None, 
                     date_to: Optional[datetime] = None) -> List[Dict]:
        """Search for photos by filename or date range"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        where_conditions = []
        params = []
        
        if query:
            where_conditions.append("filename LIKE ?")
            params.append(f"%{query}%")
        
        if date_from:
            where_conditions.append("timestamp >= ?")
            params.append(date_from.isoformat())
        
        if date_to:
            where_conditions.append("timestamp <= ?")
            params.append(date_to.isoformat())
        
        where_clause = " AND ".join(where_conditions)
        sql = "SELECT * FROM photos"
        
        if where_conditions:
            sql += f" WHERE {where_clause}"
        
        sql += " ORDER BY timestamp DESC"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        photos = []
        for row in rows:
            photo_dict = dict(zip(columns, row))
            photos.append(photo_dict)
        
        conn.close()
        return photos
    
    def get_photo_by_id(self, photo_id: int) -> Optional[Dict]:
        """Get a specific photo by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM photos WHERE id = ?", (photo_id,))
        row = cursor.fetchone()
        
        if row:
            columns = [description[0] for description in cursor.description]
            photo_dict = dict(zip(columns, row))
            conn.close()
            return photo_dict
        
        conn.close()
        return None
    
    def delete_photo(self, photo_id: int) -> bool:
        """Delete a photo from library (move to trash)"""
        try:
            photo = self.get_photo_by_id(photo_id)
            if not photo:
                return False
            
            # Move file to trash using send2trash if available
            try:
                from send2trash import send2trash
                if photo['filepath']:
                    photo_path = Path(photo['filepath'])
                    if photo_path.exists():
                        send2trash(str(photo_path))
                    
                    # Also delete associated video if it exists
                    if photo['video_filename']:
                        video_path = photo_path.parent / photo['video_filename']
                        if video_path.exists():
                            send2trash(str(video_path))
            except ImportError:
                # If send2trash is not available, remove permanently
                photo_path = Path(photo['filepath'])
                if photo_path.exists():
                    os.remove(str(photo_path))
                
                # Also delete associated video if it exists
                if photo['video_filename']:
                    video_path = photo_path.parent / photo['video_filename']
                    if video_path.exists():
                        os.remove(str(video_path))
            
            # Remove from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
            conn.commit()
            conn.close()
            
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get library statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM photos")
        total_photos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM photos WHERE has_video = 1")
        live_photos = cursor.fetchone()[0]
        
        # Calculate total size
        total_size = 0
        photos = self.get_all_photos()
        for photo in photos:
            if photo['filepath'] and os.path.exists(photo['filepath']):
                total_size += os.path.getsize(photo['filepath'])
            
            # Add video size if exists
            if photo['video_filename']:
                video_path = Path(photo['filepath']).parent / photo['video_filename']
                if video_path.exists():
                    total_size += os.path.getsize(str(video_path))
        
        conn.close()
        
        return {
            'total_photos': total_photos,
            'live_photos': live_photos,
            'total_size_bytes': total_size,
            'total_size_gb': round(total_size / (1024**3), 2)
        }
    
    def update_photo_duration(self, photo_id: int, duration: float):
        """Update the duration of a photo's video"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE photos SET duration = ? WHERE id = ?", (duration, photo_id))
        conn.commit()
        conn.close()