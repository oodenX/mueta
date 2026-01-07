# src/mueta/core/config.py
from tomllib import loads
from pathlib import Path
from pydantic_settings import BaseSettings
import platformdirs
import os

class LastFmSettings(BaseSettings):
    api_key: str = ""
    api_secret: str = ""
    enable: bool = False
    cache_ttl: int = 604800

class MLSettings(BaseSettings):
    """Machine Learning model settings."""
    enable: bool = True  # Enable ML-based genre/mood prediction as fallback
    model_dir: str = ""  # Custom model directory (default: ~/.mueta/models/)
    genre_threshold: float = 0.1  # Minimum probability threshold for genre prediction
    mood_threshold: float = 0.3  # Minimum probability threshold for mood prediction
    max_genres: int = 5  # Maximum number of genres to return
    max_moods: int = 3  # Maximum number of moods to return

class Settings(BaseSettings):
    app_name: str = "Mueta"
    debug: bool = False
    audio_save_dir : str
    lyrics_save_dir : str
    acoustid_api_key: str
    genius_api_key: str | None = None

    lastfm: LastFmSettings = LastFmSettings()
    ml: MLSettings = MLSettings()

    # Retry configuration
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0

    # Processing configuration
    default_workers: int = 3

    @staticmethod
    def _get_config_path() -> Path:
        # Check environment variable first
        env_config = os.environ.get("MUETA_CONFIG_PATH")
        if env_config:
            path = Path(env_config)
            if path.exists():
                return path

        dev_config = Path(__file__).resolve().parents[3] / "config.toml"
        if dev_config.exists():
            return dev_config

        config_dir = Path(platformdirs.user_config_dir("mueta"))
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.toml"

    @staticmethod
    def _expand_path(path_str: str) -> str:
        # Expand ~ and environment variables in path.
        return str(Path(path_str).expanduser().resolve())

    @classmethod
    def load_from_file(cls) -> "Settings":
        config_path = cls._get_config_path()
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = loads(f.read())
                # Flatten nested configuration
                settings_dict = {}
                if "default" in config_data:
                    settings_dict.update(config_data["default"])
                if "acoustid" in config_data:
                    settings_dict.update(config_data["acoustid"])
                if "genius" in config_data:
                    settings_dict.update(config_data["genius"])
                if "retry" in config_data:
                    settings_dict.update(config_data["retry"])
                if "processing" in config_data:
                    settings_dict.update(config_data["processing"])

                # Handle Last.fm nested config
                if "lastfm" in config_data:
                    settings_dict["lastfm"] = LastFmSettings(**config_data["lastfm"])

                # Handle ML nested config
                if "ml" in config_data:
                    ml_config = config_data["ml"].copy()
                    # Expand model_dir path if specified
                    if "model_dir" in ml_config and ml_config["model_dir"]:
                        ml_config["model_dir"] = cls._expand_path(ml_config["model_dir"])
                    settings_dict["ml"] = MLSettings(**ml_config)

                # Expand paths with ~ to absolute paths
                if "audio_save_dir" in settings_dict:
                    settings_dict["audio_save_dir"] = cls._expand_path(settings_dict["audio_save_dir"])
                if "lyrics_save_dir" in settings_dict:
                    settings_dict["lyrics_save_dir"] = cls._expand_path(settings_dict["lyrics_save_dir"])

                return cls(**settings_dict)
        return cls() # type: ignore


settings = Settings.load_from_file()
