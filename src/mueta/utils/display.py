# src/mueta/utils/display.py
"""Display utilities for terminal output."""

from pathlib import Path
from io import BytesIO
from PIL import Image
from rich.console import Console


def display_cover_art(image_data: bytes, width: int = 128, console: Console | None = None) -> None:
    """
    Display cover art in terminal using Unicode block characters.

    Args:
        image_data: Image data bytes.
        width: Display width in characters.
        console: Rich console instance (optional).
    """
    try:
        # Load image
        img = Image.open(BytesIO(image_data))

        # Calculate height to maintain aspect ratio
        # Unicode half-block is roughly 1:2 (width:height)
        aspect_ratio = img.height / img.width
        height = int(width * aspect_ratio / 2)

        # Resize image
        img = img.resize((width, height * 2), Image.Resampling.LANCZOS)
        img = img.convert('RGB')

        # Get pixel data
        pixels = img.load()

        # Unicode half blocks
        upper_half_block = '▀'

        # Build output - print directly to bypass Rich
        for y in range(0, height * 2, 2):
            line = []
            for x in range(width):
                # Get top and bottom pixel colors
                r1, g1, b1 = pixels[x, y] # type: ignore
                r2, g2, b2 = pixels[x, min(y + 1, height * 2 - 1)] # type: ignore

                # Create ANSI color codes
                # Top half = foreground, bottom half = background
                fg = f"\033[38;2;{r1};{g1};{b1}m"
                bg = f"\033[48;2;{r2};{g2};{b2}m"
                reset = "\033[0m"

                line.append(f"{fg}{bg}{upper_half_block}{reset}")

            # Print directly to stdout to preserve ANSI codes
            print(''.join(line))

    except Exception as e:
        if console:
            console.print(f"[yellow]⚠️ Could not display cover art: {e}[/yellow]")
        else:
            print(f"⚠️ Could not display cover art: {e}")


def extract_cover_from_file(file_path: Path) -> bytes | None:
    """
    Extract cover art from audio file.

    Args:
        file_path: Path to audio file.

    Returns:
        Image data bytes or None if no cover found.
    """
    from mutagen._file import File
    from mutagen.id3 import ID3
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4

    suffix = file_path.suffix.lower()

    try:
        if suffix == '.mp3':
            audio = ID3(file_path)
            for key in audio.keys():
                if key.startswith('APIC'):
                    return audio[key].data

        elif suffix == '.flac':
            audio = FLAC(file_path)
            if audio.pictures:
                return audio.pictures[0].data

        elif suffix in ('.m4a', '.mp4', '.aac'):
            audio = MP4(file_path)
            if 'covr' in audio:
                return bytes(audio['covr'][0])

    except Exception:
        pass

    return None
