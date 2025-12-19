# src/mueta/cli/completion.py
"""Completer for mueta CLI commands."""
import os
from pathlib import Path
from typing import List

class Completer:
    """Completer for mueta CLI commands"""

    @staticmethod
    def complete_audio_files(incomplete: str) -> List[str]:
        """Complete audio file paths"""
        audio_extensions = {'.mp3', '.flac', '.aac', '.ogg', '.m4a'}

        # Get directory and file prefix
        dir_path = os.path.dirname(incomplete) or '.'
        file_prefix = os.path.basename(incomplete)

        # Check if directory exists
        if not os.path.isdir(dir_path):
            return []

        # Find matching audio files
        matches = []
        try:
            for item in os.listdir(dir_path):
                full_path = os.path.join(dir_path, item)
                if item.startswith(file_prefix):
                    if os.path.isfile(full_path):
                        ext = Path(full_path).suffix.lower()
                        if ext in audio_extensions:
                            matches.append(full_path)
                    elif os.path.isdir(full_path):
                        matches.append(full_path + '/')
        except PermissionError:
            pass

        return sorted(matches)

    @staticmethod
    def complete_folders(incomplete: str) -> List[str]:
        """Complete folder paths"""
        dir_path = os.path.dirname(incomplete) or '.'
        folder_prefix = os.path.basename(incomplete)

        if not os.path.isdir(dir_path):
            return []

        matches = []
        try:
            for item in os.listdir(dir_path):
                if item.startswith(folder_prefix):
                    full_path = os.path.join(dir_path, item)
                    if os.path.isdir(full_path):
                        matches.append(full_path + '/')
        except PermissionError:
            pass

        return sorted(matches)
