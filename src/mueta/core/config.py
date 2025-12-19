# src/mueta/core/config.py
from tomllib import loads
from pathlib import Path
from pydantic_settings import BaseSettings
import platformdirs

class Settings(BaseSettings):
    app_name: str = "Mueta"
    debug: bool = False
    audio_save_dir : str
    lyrics_save_dir : str
    acoustid_api_key: str

    @staticmethod
    def _get_config_path() -> Path:
        dev_config = Path(__file__).resolve().parents[3] / "config.toml"
        if dev_config.exists():
            return dev_config

        config_dir = Path(platformdirs.user_config_dir("mueta"))
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.toml"

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
                return cls(**settings_dict)
        return cls() # type: ignore


settings = Settings.load_from_file()
