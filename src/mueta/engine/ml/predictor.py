# src/mueta/engine/ml/predictor.py
"""ML-based audio classification using Essentia TensorFlow models."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from mueta.core.config import settings
from mueta.engine.ml.models import (
    ModelManager,
    DISCOGS400_GENRE_MAPPING,
    MTG_JAMENDO_MOOD_MAPPING,
)

logger = logging.getLogger(__name__)

# Check for Essentia TensorFlow support
try:
    import essentia.standard as es
    
    # Configure Essentia logging based on debug setting
    if hasattr(es, 'log'):
        # Suppress Essentia logs unless in debug mode
        log_active = settings.debug
        es.log.infoActive = log_active
        es.log.warningActive = log_active
        
    from essentia.standard import (
        MonoLoader,
        TensorflowPredictEffnetDiscogs,
        TensorflowPredict2D,
    )
    HAS_ESSENTIA_TF = True
except ImportError:
    HAS_ESSENTIA_TF = False
    logger.warning("Essentia TensorFlow support not available. ML features disabled.")

# Sample rate required by the models
MODEL_SAMPLE_RATE = 16000


class MLPredictor:
    """ML-based audio classification using Essentia TensorFlow models."""

    def __init__(self, model_manager: Optional[ModelManager] = None):
        """Initialize ML predictor.

        Args:
            model_manager: Optional ModelManager instance.
        """
        self.enabled = HAS_ESSENTIA_TF
        self.model_manager = model_manager or ModelManager()
        self._embedding_model = None
        self._genre_model = None
        self._mood_model = None
        self._mood_binary_models: Dict[str, object] = {}

    def _get_embedding_model(self):
        """Lazy load the embedding model."""
        if not self.enabled:
            return None

        if self._embedding_model is None:
            model_path = self.model_manager.get_model_path("discogs-effnet")
            if model_path:
                try:
                    self._embedding_model = TensorflowPredictEffnetDiscogs(
                        graphFilename=str(model_path),
                        output="PartitionedCall:1"
                    )
                    logger.info("Loaded embedding model: discogs-effnet")
                except Exception as e:
                    logger.error(f"Failed to load embedding model: {e}")

        return self._embedding_model

    def _get_genre_model(self):
        """Lazy load the genre classification model."""
        if not self.enabled:
            return None

        if self._genre_model is None:
            model_path = self.model_manager.get_model_path("genre-discogs400")
            if model_path:
                try:
                    self._genre_model = TensorflowPredict2D(
                        graphFilename=str(model_path),
                        input="serving_default_model_Placeholder",
                        output="PartitionedCall:0"
                    )
                    logger.info("Loaded genre model: genre-discogs400")
                except Exception as e:
                    logger.error(f"Failed to load genre model: {e}")

        return self._genre_model

    def _get_mood_model(self):
        """Lazy load the mood/theme classification model."""
        if not self.enabled:
            return None

        if self._mood_model is None:
            model_path = self.model_manager.get_model_path("mood-mtg-jamendo")
            if model_path:
                try:
                    self._mood_model = TensorflowPredict2D(
                        graphFilename=str(model_path)
                    )
                    logger.info("Loaded mood model: mood-mtg-jamendo")
                except Exception as e:
                    logger.error(f"Failed to load mood model: {e}")

        return self._mood_model

    def _get_mood_binary_model(self, mood_name: str):
        """Lazy load a binary mood classifier.

        Args:
            mood_name: One of 'happy', 'sad', 'relaxed', 'aggressive', 'party'
        """
        if not self.enabled:
            return None

        model_key = f"mood-{mood_name}"

        if model_key not in self._mood_binary_models:
            model_path = self.model_manager.get_model_path(model_key)
            if model_path:
                try:
                    self._mood_binary_models[model_key] = TensorflowPredict2D(
                        graphFilename=str(model_path),
                        output="model/Softmax"
                    )
                    logger.info(f"Loaded binary mood model: {model_key}")
                except Exception as e:
                    logger.error(f"Failed to load {model_key}: {e}")
                    self._mood_binary_models[model_key] = None

        return self._mood_binary_models.get(model_key)

    def _load_audio(self, file_path: Path | str) -> Optional[object]:
        """Load audio file at the required sample rate.

        Args:
            file_path: Path to audio file.

        Returns:
            Audio array, or None if loading failed.
        """
        if not self.enabled:
            return None

        try:
            loader = MonoLoader(
                filename=str(file_path),
                sampleRate=MODEL_SAMPLE_RATE,
                resampleQuality=4
            )
            return loader()
        except Exception as e:
            logger.error(f"Failed to load audio for ML: {e}")
            return None

    def _extract_embeddings(self, audio) -> Optional[object]:
        """Extract embeddings from audio.

        Args:
            audio: Audio array at 16kHz.

        Returns:
            Embedding array, or None if extraction failed.
        """
        embedding_model = self._get_embedding_model()
        if embedding_model is None:
            return None

        try:
            return embedding_model(audio)
        except Exception as e:
            logger.error(f"Failed to extract embeddings: {e}")
            return None

    def predict_genre(
        self,
        file_path: Path | str,
        top_k: int = 5,
        threshold: float = 0.1
    ) -> List[str]:
        """Predict genres from audio file.

        Args:
            file_path: Path to audio file.
            top_k: Maximum number of genres to return.
            threshold: Minimum probability threshold for genres.

        Returns:
            List of predicted genre names (mapped to our taxonomy).
        """
        if not self.enabled:
            return []

        # Load audio
        audio = self._load_audio(file_path)
        if audio is None:
            return []

        # Extract embeddings
        embeddings = self._extract_embeddings(audio)
        if embeddings is None:
            return []

        # Get genre predictions
        genre_model = self._get_genre_model()
        if genre_model is None:
            return []

        try:
            predictions = genre_model(embeddings)

            # Get class names
            classes = self.model_manager.get_genre_classes()
            if not classes:
                logger.warning("Genre classes not available")
                return []

            # Average predictions across time frames
            import numpy as np
            avg_predictions = np.mean(predictions, axis=0)

            # Get top predictions
            top_indices = np.argsort(avg_predictions)[::-1][:top_k * 3]  # Get more to filter

            # Map to our taxonomy genres
            predicted_genres = set()
            for idx in top_indices:
                if avg_predictions[idx] < threshold:
                    continue

                class_name = classes[idx] if idx < len(classes) else None
                if class_name:
                    # Try to map to our taxonomy
                    mapped = DISCOGS400_GENRE_MAPPING.get(class_name)
                    if mapped:
                        predicted_genres.add(mapped)
                    else:
                        # Check partial matches
                        for discogs_genre, our_genre in DISCOGS400_GENRE_MAPPING.items():
                            if discogs_genre.lower() in class_name.lower():
                                predicted_genres.add(our_genre)
                                break

                if len(predicted_genres) >= top_k:
                    break

            result = sorted(list(predicted_genres))
            logger.info(f"ML genre prediction for {Path(file_path).name}: {result}")
            return result

        except Exception as e:
            logger.error(f"Genre prediction failed: {e}")
            return []

    def predict_mood(
        self,
        file_path: Path | str,
        top_k: int = 3,
        threshold: float = 0.3
    ) -> List[str]:
        """Predict moods from audio file.

        Args:
            file_path: Path to audio file.
            top_k: Maximum number of moods to return.
            threshold: Minimum probability threshold for moods.

        Returns:
            List of predicted mood names (mapped to our taxonomy).
        """
        if not self.enabled:
            return []

        # Load audio
        audio = self._load_audio(file_path)
        if audio is None:
            return []

        # Extract embeddings
        embeddings = self._extract_embeddings(audio)
        if embeddings is None:
            return []

        predicted_moods = set()

        # Method 1: Use MTG-Jamendo mood/theme model (multi-label)
        mood_model = self._get_mood_model()
        if mood_model is not None:
            try:
                predictions = mood_model(embeddings)
                classes = self.model_manager.get_mood_classes()

                if classes:
                    import numpy as np
                    avg_predictions = np.mean(predictions, axis=0)

                    # Multi-label: get all classes above threshold
                    for idx, prob in enumerate(avg_predictions):
                        if prob >= threshold and idx < len(classes):
                            class_name = classes[idx].lower()
                            mapped = MTG_JAMENDO_MOOD_MAPPING.get(class_name)
                            if mapped:
                                predicted_moods.add(mapped)

            except Exception as e:
                logger.warning(f"MTG-Jamendo mood prediction failed: {e}")

        # Method 2: Use binary mood classifiers for higher accuracy
        binary_moods = ["happy", "sad", "relaxed", "aggressive", "party"]
        mood_mapping = {
            "happy": "Happy",
            "sad": "Sad",
            "relaxed": "Chill",
            "aggressive": "Aggressive",
            "party": "Party"
        }

        for mood in binary_moods:
            model = self._get_mood_binary_model(mood)
            if model is not None:
                try:
                    predictions = model(embeddings)
                    import numpy as np
                    avg_pred = np.mean(predictions, axis=0)

                    # Binary classifier: [not_mood, mood]
                    if len(avg_pred) >= 2 and avg_pred[1] >= threshold:
                        predicted_moods.add(mood_mapping[mood])

                except Exception as e:
                    logger.warning(f"Binary mood prediction failed for {mood}: {e}")

        result = sorted(list(predicted_moods))[:top_k]
        logger.info(f"ML mood prediction for {Path(file_path).name}: {result}")
        return result

    def predict_all(
        self,
        file_path: Path | str
    ) -> Dict[str, List[str]]:
        """Predict both genres and moods from audio file.

        Args:
            file_path: Path to audio file.

        Returns:
            Dict with 'genres' and 'moods' lists.
        """
        return {
            "genres": self.predict_genre(file_path),
            "moods": self.predict_mood(file_path)
        }

    def is_available(self) -> bool:
        """Check if ML prediction is available.

        Returns:
            True if Essentia TensorFlow support is available.
        """
        return self.enabled
