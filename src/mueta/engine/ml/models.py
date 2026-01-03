# src/mueta/engine/ml/models.py
"""Model download and management for Essentia TensorFlow models."""

import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional

import httpx
import platformdirs
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn

logger = logging.getLogger(__name__)
console = Console()

# Model definitions with URLs and metadata
# Using discogs-effnet as the embedding model (best overall performance)
MODELS = {
    # Embedding model (required for all predictions)
    "discogs-effnet": {
        "url": "https://essentia.upf.edu/models/feature-extractors/discogs-effnet/discogs-effnet-bs64-1.pb",
        "filename": "discogs-effnet-bs64-1.pb",
        "description": "Discogs EfficientNet embedding model",
        "size_mb": 16,
    },
    # Genre classification (400 music styles from Discogs)
    "genre-discogs400": {
        "url": "https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.pb",
        "filename": "genre_discogs400-discogs-effnet-1.pb",
        "description": "Genre classifier (400 styles from Discogs)",
        "size_mb": 1,
        "classes_url": "https://essentia.upf.edu/models/classification-heads/genre_discogs400/genre_discogs400-discogs-effnet-1.json",
    },
    # MTG-Jamendo mood/theme (56 classes, multi-label)
    "mood-mtg-jamendo": {
        "url": "https://essentia.upf.edu/models/classification-heads/mtg_jamendo_moodtheme/mtg_jamendo_moodtheme-discogs-effnet-1.pb",
        "filename": "mtg_jamendo_moodtheme-discogs-effnet-1.pb",
        "description": "Mood/theme classifier (56 classes from MTG-Jamendo)",
        "size_mb": 1,
        "classes_url": "https://essentia.upf.edu/models/classification-heads/mtg_jamendo_moodtheme/mtg_jamendo_moodtheme-discogs-effnet-1.json",
    },
    # Individual mood classifiers (binary)
    "mood-happy": {
        "url": "https://essentia.upf.edu/models/classification-heads/mood_happy/mood_happy-discogs-effnet-1.pb",
        "filename": "mood_happy-discogs-effnet-1.pb",
        "description": "Mood happy classifier (binary)",
        "size_mb": 1,
    },
    "mood-sad": {
        "url": "https://essentia.upf.edu/models/classification-heads/mood_sad/mood_sad-discogs-effnet-1.pb",
        "filename": "mood_sad-discogs-effnet-1.pb",
        "description": "Mood sad classifier (binary)",
        "size_mb": 1,
    },
    "mood-relaxed": {
        "url": "https://essentia.upf.edu/models/classification-heads/mood_relaxed/mood_relaxed-discogs-effnet-1.pb",
        "filename": "mood_relaxed-discogs-effnet-1.pb",
        "description": "Mood relaxed classifier (binary)",
        "size_mb": 1,
    },
    "mood-aggressive": {
        "url": "https://essentia.upf.edu/models/classification-heads/mood_aggressive/mood_aggressive-discogs-effnet-1.pb",
        "filename": "mood_aggressive-discogs-effnet-1.pb",
        "description": "Mood aggressive classifier (binary)",
        "size_mb": 1,
    },
    "mood-party": {
        "url": "https://essentia.upf.edu/models/classification-heads/mood_party/mood_party-discogs-effnet-1.pb",
        "filename": "mood_party-discogs-effnet-1.pb",
        "description": "Mood party classifier (binary)",
        "size_mb": 1,
    },
}

# Genre mapping from Discogs400 to simplified categories
# This maps the 400 Discogs styles to our taxonomy genres
DISCOGS400_GENRE_MAPPING = {
    # Electronic genres
    "Electronic": "Electronic",
    "House": "Electronic",
    "Techno": "Electronic",
    "Trance": "Electronic",
    "Ambient": "Electronic",
    "Downtempo": "Electronic",
    "Electro": "Electronic",
    "Drum n Bass": "Electronic",
    "Dubstep": "Electronic",
    "IDM": "Electronic",
    "Industrial": "Electronic",
    "Synth-pop": "Electronic",
    "EBM": "Electronic",
    "New Wave": "Electronic",
    
    # Rock genres
    "Rock": "Rock",
    "Alternative Rock": "Rock",
    "Indie Rock": "Rock",
    "Hard Rock": "Rock",
    "Punk": "Rock",
    "Grunge": "Rock",
    "Progressive Rock": "Rock",
    "Psychedelic Rock": "Rock",
    "Post-Rock": "Rock",
    "Garage Rock": "Rock",
    "Classic Rock": "Rock",
    
    # Metal genres
    "Heavy Metal": "Metal",
    "Thrash": "Metal",
    "Death Metal": "Metal",
    "Black Metal": "Metal",
    "Doom Metal": "Metal",
    "Power Metal": "Metal",
    "Metalcore": "Metal",
    "Nu Metal": "Metal",
    
    # Pop genres
    "Pop": "Pop",
    "Pop Rock": "Pop",
    "Synth-pop": "Pop",
    "Dance-pop": "Pop",
    "Europop": "Pop",
    "J-Pop": "Pop",
    "K-Pop": "Pop",
    
    # Hip-Hop genres
    "Hip Hop": "Hip-Hop",
    "Rap": "Hip-Hop",
    "Trap": "Hip-Hop",
    "Boom Bap": "Hip-Hop",
    "Gangsta": "Hip-Hop",
    "Trip Hop": "Hip-Hop",
    
    # R&B genres
    "Soul": "R&B",
    "Funk": "R&B",
    "Disco": "R&B",
    "Contemporary R&B": "R&B",
    "Neo Soul": "R&B",
    "Motown": "R&B",
    
    # Jazz genres
    "Jazz": "Jazz",
    "Smooth Jazz": "Jazz",
    "Fusion": "Jazz",
    "Bebop": "Jazz",
    "Cool Jazz": "Jazz",
    "Free Jazz": "Jazz",
    "Latin Jazz": "Jazz",
    
    # Classical genres
    "Classical": "Classical",
    "Baroque": "Classical",
    "Romantic": "Classical",
    "Modern Classical": "Classical",
    "Opera": "Classical",
    "Orchestral": "Classical",
    
    # Folk genres
    "Folk": "Folk",
    "Acoustic": "Folk",
    "Folk Rock": "Folk",
    "Country": "Folk",
    "Bluegrass": "Folk",
    "Americana": "Folk",
    
    # Blues genres
    "Blues": "Blues",
    "Electric Blues": "Blues",
    "Delta Blues": "Blues",
    "Blues Rock": "Blues",
    
    # Reggae genres
    "Reggae": "Reggae",
    "Ska": "Reggae",
    "Dub": "Reggae",
    "Dancehall": "Reggae",
    "Rocksteady": "Reggae",
    
    # Latin genres
    "Latin": "Latin",
    "Salsa": "Latin",
    "Bossa Nova": "Latin",
    "Reggaeton": "Latin",
    "Latin Pop": "Latin",
    "Tango": "Latin",
    
    # World genres
    "World": "World",
    "African": "World",
    "Celtic": "World",
    "Middle Eastern": "World",
    "Indian Classical": "World",
    
    # Soundtrack
    "Soundtrack": "Soundtrack",
    "Score": "Soundtrack",
    "Video Game Music": "Soundtrack",
}

# MTG-Jamendo mood/theme classes mapping to our taxonomy
MTG_JAMENDO_MOOD_MAPPING = {
    "happy": "Happy",
    "sad": "Sad",
    "relaxing": "Chill",
    "calm": "Chill",
    "meditative": "Chill",
    "aggressive": "Aggressive",
    "dark": "Dark",
    "energetic": "Energetic",
    "powerful": "Energetic",
    "upbeat": "Energetic",
    "romantic": "Romantic",
    "love": "Romantic",
    "party": "Party",
    "fun": "Party",
    "motivational": "Energetic",
    "inspiring": "Energetic",
    "melancholic": "Sad",
    "emotional": "Romantic",
    "dramatic": "Dark",
    "epic": "Energetic",
}


class ModelManager:
    """Manages downloading and caching of Essentia TensorFlow models."""
    
    def __init__(self, model_dir: Optional[Path] = None):
        """Initialize model manager.
        
        Args:
            model_dir: Custom model directory. Defaults to ~/.mueta/models/
        """
        if model_dir:
            self.model_dir = Path(model_dir)
        else:
            self.model_dir = Path(platformdirs.user_data_dir("mueta")) / "models"
        
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._loaded_classes: Dict[str, list] = {}
    
    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Get path to a model, downloading if necessary.
        
        Args:
            model_name: Name of the model (e.g., 'discogs-effnet', 'genre-discogs400')
            
        Returns:
            Path to the model file, or None if download failed.
        """
        if model_name not in MODELS:
            logger.error(f"Unknown model: {model_name}")
            return None
        
        model_info = MODELS[model_name]
        model_path = self.model_dir / model_info["filename"]
        
        if model_path.exists():
            return model_path
        
        # Download model
        logger.info(f"Downloading model: {model_name} ({model_info['description']})")
        
        if self._download_file(model_info["url"], model_path, model_info.get("size_mb", 0)):
            # Also download classes JSON if available
            if "classes_url" in model_info:
                classes_path = model_path.with_suffix(".json")
                self._download_file(model_info["classes_url"], classes_path, 0)
            return model_path
        
        return None
    
    def _download_file(self, url: str, dest_path: Path, size_mb: int) -> bool:
        """Download a file with progress bar.
        
        Args:
            url: URL to download from.
            dest_path: Destination path.
            size_mb: Approximate size in MB (for display).
            
        Returns:
            True if download succeeded.
        """
        try:
            with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length", 0))
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    console=console,
                    transient=True,
                ) as progress:
                    task = progress.add_task(
                        f"Downloading {dest_path.name}...",
                        total=total if total else None
                    )
                    
                    with open(dest_path, "wb") as f:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))
                
                logger.info(f"Downloaded: {dest_path.name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            if dest_path.exists():
                dest_path.unlink()
            return False
    
    def get_genre_classes(self) -> list:
        """Get list of genre classes for the genre model.
        
        Returns:
            List of genre class names in order.
        """
        if "genre_classes" in self._loaded_classes:
            return self._loaded_classes["genre_classes"]
        
        classes_path = self.model_dir / "genre_discogs400-discogs-effnet-1.json"
        
        if not classes_path.exists():
            # Try to download
            model_info = MODELS.get("genre-discogs400", {})
            if "classes_url" in model_info:
                self._download_file(model_info["classes_url"], classes_path, 0)
        
        if classes_path.exists():
            import json
            with open(classes_path, "r") as f:
                data = json.load(f)
                classes = data.get("classes", [])
                self._loaded_classes["genre_classes"] = classes
                return classes
        
        return []
    
    def get_mood_classes(self) -> list:
        """Get list of mood/theme classes for the mood model.
        
        Returns:
            List of mood class names in order.
        """
        if "mood_classes" in self._loaded_classes:
            return self._loaded_classes["mood_classes"]
        
        classes_path = self.model_dir / "mtg_jamendo_moodtheme-discogs-effnet-1.json"
        
        if not classes_path.exists():
            model_info = MODELS.get("mood-mtg-jamendo", {})
            if "classes_url" in model_info:
                self._download_file(model_info["classes_url"], classes_path, 0)
        
        if classes_path.exists():
            import json
            with open(classes_path, "r") as f:
                data = json.load(f)
                classes = data.get("classes", [])
                self._loaded_classes["mood_classes"] = classes
                return classes
        
        return []
    
    def ensure_models_downloaded(self, model_names: list[str]) -> bool:
        """Ensure all specified models are downloaded.
        
        Args:
            model_names: List of model names to download.
            
        Returns:
            True if all models are available.
        """
        all_ok = True
        for name in model_names:
            if self.get_model_path(name) is None:
                all_ok = False
        return all_ok
    
    def list_available_models(self) -> Dict[str, dict]:
        """List all available models with their status.
        
        Returns:
            Dict mapping model name to status info.
        """
        result = {}
        for name, info in MODELS.items():
            model_path = self.model_dir / info["filename"]
            result[name] = {
                "description": info["description"],
                "downloaded": model_path.exists(),
                "size_mb": info.get("size_mb", 0),
                "path": str(model_path) if model_path.exists() else None,
            }
        return result
