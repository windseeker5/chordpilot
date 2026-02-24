#!/usr/bin/env python3
"""
Helper script to add a new song to the Guitar Practice App
"""
import json
import os
import sys


def add_song():
    """Interactive script to add a new song"""
    print("=== Add New Song to Guitar Practice App ===\n")

    # Get song details
    title = input("Song title: ").strip()
    if not title:
        print("Error: Title is required")
        return

    artist = input("Artist name: ").strip()
    if not artist:
        print("Error: Artist is required")
        return

    key = input("Song key (e.g., C, G, D): ").strip().upper()

    # Generate folder name (lowercase, hyphenated)
    default_folder = title.lower().replace(' ', '-').replace("'", '')
    folder = input(f"Folder name [{default_folder}]: ").strip()
    if not folder:
        folder = default_folder

    # Generate song ID (same as folder by default)
    song_id = input(f"Song ID [{folder}]: ").strip()
    if not song_id:
        song_id = folder

    # Create folder
    song_path = os.path.join('static', 'songs', folder)
    if os.path.exists(song_path):
        print(f"\nWarning: Folder '{song_path}' already exists")
        overwrite = input("Continue anyway? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Cancelled")
            return
    else:
        os.makedirs(song_path, exist_ok=True)
        print(f"\nCreated folder: {song_path}")

    # Create template ChordPro file
    chordpro_path = os.path.join(song_path, 'chords.cho')
    if not os.path.exists(chordpro_path):
        with open(chordpro_path, 'w') as f:
            f.write(f"""{{title: {title}}}
{{artist: {artist}}}
{{key: {key}}}

{{start_of_verse}}
[C]Add your chords and [G]lyrics here
[Am]Use square brackets for [F]chords
{{end_of_verse}}

{{start_of_chorus}}
[C]This is the [G]chorus
{{end_of_chorus}}
""")
        print(f"Created template: {chordpro_path}")
    else:
        print(f"ChordPro file already exists: {chordpro_path}")

    # Check for audio file
    audio_path = os.path.join(song_path, 'audio.mp3')
    if not os.path.exists(audio_path):
        print(f"\nReminder: Add your MP3 file to: {audio_path}")

    # Update songs.json
    songs_json = 'songs.json'
    if os.path.exists(songs_json):
        with open(songs_json, 'r') as f:
            data = json.load(f)
    else:
        data = {'songs': []}

    # Check if song already exists
    existing = next((s for s in data['songs'] if s['id'] == song_id), None)
    if existing:
        print(f"\nWarning: Song with ID '{song_id}' already exists in songs.json")
        update = input("Update it? (y/n): ").strip().lower()
        if update != 'y':
            print("\nSong folder created but songs.json not updated")
            return
        # Remove existing
        data['songs'] = [s for s in data['songs'] if s['id'] != song_id]

    # Add new song
    new_song = {
        'id': song_id,
        'title': title,
        'artist': artist,
        'key': key,
        'folder': folder
    }
    data['songs'].append(new_song)

    # Write back
    with open(songs_json, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nUpdated {songs_json}")
    print("\n=== Song Added Successfully! ===")
    print(f"\nNext steps:")
    print(f"1. Edit the chords: {chordpro_path}")
    print(f"2. Add audio file: {audio_path}")
    print(f"3. Refresh your browser")


if __name__ == '__main__':
    try:
        add_song()
    except KeyboardInterrupt:
        print("\n\nCancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
