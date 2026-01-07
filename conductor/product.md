# Product Guide: Mueta

## Initial Concept
Mueta is a modern CLI application designed to automate the retrieval and management of high-quality metadata for local audio libraries. It bridges the gap between official data sources (like MusicBrainz) and advanced acoustic analysis, providing a comprehensive solution for both casual listeners and dedicated music collectors.

## Target Users
- **Music Collectors:** Users seeking a highly organized and consistent local music library with perfect tagging.
- **Casual Listeners:** Individuals who want beautiful album art and accurate basic tags without manual effort.
- **Developers:** Those looking for a modular and scriptable tool to integrate into larger media workflows or to use as a library for music metadata.

## Key Features
- **Automated Pipeline:** A robust "set-it-and-forget-it" CLI workflow that handles fingerprinting, fetching, and tagging.
- **Advanced Audio Analysis:** Integration of machine learning (Essentia) to provide technical metadata such as BPM, Key, and loudness.
- **Modern Terminal UI:** A polished user experience utilizing `rich` for beautiful status displays, progress bars, and interactive selection.
- **Flexible Data Sourcing:** Leveraging AcoustID, MusicBrainz, and Genius, with additional support for lyrics and unofficial APIs.
- **AI-Powered Attributes:** Using Large Language Models (LLMs) to determine abstract attributes like Genre and Mood.

## Primary Goals
- **Effortless Automation:** To automate the tedious process of tagging large music collections at scale.
- **Technical Insight:** To provide detailed acoustic analysis (BPM, Key, etc.) for better music discovery, playlist generation, and organization.
- **High Fidelity Accuracy:** To offer a curation-friendly workflow that allows for manual verification when needed to ensure perfect library accuracy.

## Version Roadmap
- **v0.1.0 (Core):** Implement basic functionality: Initialization, Metadata Display (`view-meta`), Fetching Metadata (`get-meta`), Lyrics Download, and Cover Art retrieval.
- **v0.2.0 (Analysis):** Implement audio feature extraction for BPM and Key using Essentia.
- **v0.3.0 (Semantic AI):** Implement abstract attribute detection for Genre and Mood using Large Language Models (LLM).

## Testing Strategy
- **Test Dataset:** 65 diverse audio tracks located in `~/test/test_audio`.
- **Configuration:**
    - Workers: `--workers 10`
    - Safety: `--reserve` (to preserve original files)
    - Output Directory: `~/test/output/`
- **Branching:** All development and testing to be conducted on the `develop` branch.
