# Tech Stack: Mueta

## Core Technologies
- **Python (>= 3.12):** The primary programming language, chosen for its extensive ecosystem of audio processing and machine learning libraries.
- **Typer & Click:** Used for building the command-line interface, providing a modern and user-friendly interaction model.
- **Pydantic & Pydantic-Settings:** Employed for robust data validation, modeling metadata structures, and managing application configuration.

## Audio Processing & Analysis
- **Mutagen:** A cross-platform Python module to handle audio metadata (ID3, Vorbis, etc.).
- **Pyacoustid:** Interface for the AcoustID web service to enable audio fingerprinting and identification.
- **Essentia:** An open-source library and tools for audio analysis and audio-based music information retrieval.
- **Essentia-TensorFlow:** Used for machine learning-based feature extraction (Mood, Genre prediction).

## Networking & UI
- **HTTPX:** A next-generation HTTP client for Python, used for making asynchronous requests to metadata APIs.
- **Rich:** A Python library for rich text and beautiful formatting in the terminal, used for status displays and interactive components.
- **Loguru:** A library which aims to make logging in Python enjoyable.

## Development & Build Tools
- **uv:** An extremely fast Python package and project manager, used for dependency resolution and environment management.
- **Ruff & Black:** Tools for high-performance linting, fixing, and formatting to maintain code quality and consistency.
- **Pytest:** The standard framework for writing and running unit and integration tests.
- **Hatchling:** The build backend used for packaging the application.
