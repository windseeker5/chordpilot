"""
YouTube audio downloader for Guitar Practice App
Uses yt-dlp to extract audio from YouTube videos
"""
import os
import re
from typing import Dict, List, Optional
import subprocess
import json


def search_youtube(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search YouTube for videos matching the query
    Returns list of video info (title, url, duration, thumbnail)
    """
    try:
        # Use yt-dlp to search
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--skip-download',
            '--default-search', 'ytsearch5',
            f'ytsearch{max_results}:{query}'
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"Error searching YouTube: {result.stderr}")
            return []

        # Parse JSON results
        videos = []
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            try:
                video_info = json.loads(line)
                videos.append({
                    'id': video_info.get('id', ''),
                    'title': video_info.get('title', ''),
                    'url': video_info.get('webpage_url', ''),
                    'duration': video_info.get('duration', 0),
                    'duration_string': video_info.get('duration_string', ''),
                    'thumbnail': video_info.get('thumbnail', ''),
                    'channel': video_info.get('channel', ''),
                    'view_count': video_info.get('view_count', 0)
                })
            except json.JSONDecodeError:
                continue

        return videos

    except subprocess.TimeoutExpired:
        print("YouTube search timed out")
        return []
    except Exception as e:
        print(f"Error searching YouTube: {e}")
        return []


def download_audio(youtube_url: str, output_path: str, progress_callback=None) -> bool:
    """
    Download audio from YouTube video

    Args:
        youtube_url: YouTube video URL
        output_path: Path to save the audio file (should end with .mp3)
        progress_callback: Optional callback function(progress_percent, status_message)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # yt-dlp options
        cmd = [
            'yt-dlp',
            '--extract-audio',
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # Best quality
            '--output', output_path.replace('.mp3', '.%(ext)s'),
            '--no-playlist',
            '--no-warnings',
            youtube_url
        ]

        if progress_callback:
            progress_callback(10, "Starting download...")

        # Run yt-dlp
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Monitor progress
        for line in process.stderr:
            if progress_callback:
                # Parse progress from yt-dlp output
                if '[download]' in line and '%' in line:
                    try:
                        match = re.search(r'(\d+\.?\d*)%', line)
                        if match:
                            percent = float(match.group(1))
                            progress_callback(int(percent), f"Downloading... {percent:.1f}%")
                    except:
                        pass
                elif '[ExtractAudio]' in line:
                    progress_callback(95, "Converting to MP3...")

        process.wait()

        if progress_callback:
            progress_callback(100, "Download complete!")

        # Check if file was created
        if os.path.exists(output_path):
            return True
        else:
            # Sometimes yt-dlp adds .mp3 extension, check for that
            possible_path = output_path.replace('.mp3', '') + '.mp3'
            if os.path.exists(possible_path) and possible_path != output_path:
                os.rename(possible_path, output_path)
                return True

        return False

    except Exception as e:
        print(f"Error downloading audio: {e}")
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return False


def get_video_info(youtube_url: str) -> Optional[Dict]:
    """
    Get information about a YouTube video without downloading
    """
    try:
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--skip-download',
            youtube_url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return None

        video_info = json.loads(result.stdout)
        return {
            'id': video_info.get('id', ''),
            'title': video_info.get('title', ''),
            'url': video_info.get('webpage_url', ''),
            'duration': video_info.get('duration', 0),
            'duration_string': video_info.get('duration_string', ''),
            'thumbnail': video_info.get('thumbnail', ''),
            'channel': video_info.get('channel', ''),
            'description': video_info.get('description', ''),
        }

    except Exception as e:
        print(f"Error getting video info: {e}")
        return None


def check_ytdlp_installed() -> bool:
    """Check if yt-dlp is installed"""
    try:
        result = subprocess.run(
            ['yt-dlp', '--version'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False


if __name__ == '__main__':
    # Test the module
    if check_ytdlp_installed():
        print("✓ yt-dlp is installed")

        # Test search
        print("\nTesting YouTube search...")
        results = search_youtube("Amazing Grace guitar tutorial")
        print(f"Found {len(results)} videos")
        for i, video in enumerate(results[:3], 1):
            print(f"{i}. {video['title']} - {video['duration_string']}")
    else:
        print("✗ yt-dlp is not installed")
        print("Install with: pip install yt-dlp")
