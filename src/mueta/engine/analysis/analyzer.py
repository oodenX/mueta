import logging
from pathlib import Path

from mueta.engine.models import AudioMetadata

logger = logging.getLogger(__name__)

try:
    import essentia.standard as es

    HAS_ESSENTIA = True
except ImportError:
    HAS_ESSENTIA = False


class AudioAnalyzer:
    """Audio analyzer using Essentia."""

    def __init__(self):
        if not HAS_ESSENTIA:
            logger.warning("Essentia not found. Analysis features will be disabled.")

    def analyze(self, file_path: Path | str) -> AudioMetadata:
        """Analyze audio file to extract BPM, Key, and other features."""
        metadata = AudioMetadata()

        if not HAS_ESSENTIA:
            return metadata

        file_path = str(file_path)
        try:
            # Load audio (mono for analysis)
            # Essentia's MonoLoader automatically downmixes and resamples to 44.1kHz by default
            loader = es.MonoLoader(filename=file_path)
            audio = loader()

            # 1. BPM (Rhythm)
            # RhythmExtractor2013 is robust
            rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
            bpm, _, _, _, _ = rhythm_extractor(audio)
            metadata.bpm = round(float(bpm), 1)

            # 2. Key & Scale (Harmony)
            # KeyExtractor
            key_extractor = es.KeyExtractor()
            key, scale, strength = key_extractor(audio)
            metadata.key = key
            metadata.scale = scale

            # 3. Loudness & Dynamics
            # LoudnessEBUR128 requires stereo, using standard Loudness for mono
            loudness_extractor = es.Loudness()
            loudness = loudness_extractor(audio)
            metadata.loudness_lufs = round(float(loudness), 2)
            # metadata.dynamic_range = ... # Not available in standard Loudness

            # 4. Danceability
            danceability_extractor = es.Danceability()
            danceability, _ = danceability_extractor(audio)
            metadata.danceability = round(float(danceability), 3)

            logger.info(
                f"Analyzed {Path(file_path).name}: BPM={metadata.bpm}, Key={metadata.key} {metadata.scale}"
            )

        except Exception as e:
            logger.error(f"Analysis failed for {file_path}: {e}")

        return metadata
