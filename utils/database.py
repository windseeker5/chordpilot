"""
Database module for Guitar Practice App
Uses SQLite3 for storing song metadata
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


DB_PATH = 'guitprac.db'


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def init_db():
    """Initialize database with schema"""
    conn = get_db()
    cursor = conn.cursor()

    # Songs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            key TEXT,
            folder TEXT NOT NULL,
            youtube_url TEXT,
            chords_source TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_played TIMESTAMP,
            play_count INTEGER DEFAULT 0
        )
    ''')

    # Downloads table (track download status)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            song_id TEXT NOT NULL,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (song_id) REFERENCES songs(song_id)
        )
    ''')

    conn.commit()
    conn.close()
    print("✓ Database initialized")


def migrate_from_json():
    """Migrate existing songs.json to database"""
    if not os.path.exists('songs.json'):
        print("No songs.json found, skipping migration")
        return

    with open('songs.json', 'r') as f:
        data = json.load(f)

    conn = get_db()
    cursor = conn.cursor()

    migrated = 0
    for song in data.get('songs', []):
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO songs (song_id, title, artist, key, folder)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                song['id'],
                song['title'],
                song['artist'],
                song.get('key', ''),
                song['folder']
            ))
            if cursor.rowcount > 0:
                migrated += 1
        except Exception as e:
            print(f"Error migrating song {song.get('title')}: {e}")

    conn.commit()
    conn.close()

    if migrated > 0:
        print(f"✓ Migrated {migrated} songs from songs.json")
        # Backup the JSON file
        os.rename('songs.json', 'songs.json.backup')
        print("✓ Backed up songs.json to songs.json.backup")


def get_all_songs() -> List[Dict]:
    """Get all songs from database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM songs ORDER BY title')
    songs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return songs


def get_song_by_id(song_id: str) -> Optional[Dict]:
    """Get a single song by ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM songs WHERE song_id = ?', (song_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def add_song(song_data: Dict) -> str:
    """
    Add a new song to database
    Returns the song_id
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO songs (song_id, title, artist, key, folder, youtube_url, chords_source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        song_data['song_id'],
        song_data['title'],
        song_data['artist'],
        song_data.get('key', ''),
        song_data['folder'],
        song_data.get('youtube_url', ''),
        song_data.get('chords_source', '')
    ))

    conn.commit()
    conn.close()

    return song_data['song_id']


def update_song(song_id: str, updates: Dict):
    """Update a song's metadata"""
    conn = get_db()
    cursor = conn.cursor()

    # Build SET clause dynamically
    set_clauses = []
    values = []
    for key, value in updates.items():
        set_clauses.append(f"{key} = ?")
        values.append(value)

    values.append(song_id)

    query = f"UPDATE songs SET {', '.join(set_clauses)} WHERE song_id = ?"
    cursor.execute(query, values)

    conn.commit()
    conn.close()


def delete_song(song_id: str):
    """Delete a song from database"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM songs WHERE song_id = ?', (song_id,))
    conn.commit()
    conn.close()


def record_play(song_id: str):
    """Record that a song was played"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE songs
        SET play_count = play_count + 1,
            last_played = CURRENT_TIMESTAMP
        WHERE song_id = ?
    ''', (song_id,))

    conn.commit()
    conn.close()


def create_download_record(song_id: str) -> int:
    """Create a download record and return its ID"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO downloads (song_id, status, progress)
        VALUES (?, 'pending', 0)
    ''', (song_id,))

    download_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return download_id


def update_download_status(download_id: int, status: str, progress: int = None, error: str = None):
    """Update download status"""
    conn = get_db()
    cursor = conn.cursor()

    if error:
        cursor.execute('''
            UPDATE downloads
            SET status = ?, error_message = ?
            WHERE id = ?
        ''', (status, error, download_id))
    elif progress is not None:
        cursor.execute('''
            UPDATE downloads
            SET status = ?, progress = ?
            WHERE id = ?
        ''', (status, progress, download_id))
    else:
        cursor.execute('''
            UPDATE downloads
            SET status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, download_id))

    conn.commit()
    conn.close()


def get_download_status(song_id: str) -> Optional[Dict]:
    """Get latest download status for a song"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM downloads
        WHERE song_id = ?
        ORDER BY started_at DESC
        LIMIT 1
    ''', (song_id,))

    row = cursor.fetchone()
    conn.close()

    return dict(row) if row else None


if __name__ == '__main__':
    # Initialize database
    init_db()
    migrate_from_json()
