# Product Guidelines: Mueta

## CLI Communication Style
- **Informative & Professional:** Mueta should provide clear, technical status updates. The user should always know what stage of the pipeline the program is in (e.g., "Fingerprinting audio...", "Querying MusicBrainz...", "Fetching Lyrics...").
- **Clear Error Handling:** Failures should be reported with enough detail to understand the cause (e.g., API key missing, network timeout) without cluttering the output.

## Visual Identity & UX
- **High-Contrast Modern:** Utilize the `rich` library to create a visually distinct experience. Use bold colors for headers, dim colors for secondary data, and consistent color coding for status (e.g., Green for success, Red for failure, Blue for info).
- **Structured Metadata Display:** Metadata should be presented in organized tables or panels to ensure readability even when multiple fields are retrieved.
- **Interactive Feedback:** For ambiguous matches, provide a clean, numbered list for user selection.

## Core Development Principles
- **Robustness (Safety First):**
    - Implement aggressive retry logic for network requests.
    - Validate all API responses before attempting to write to files.
    - Ensure a "fail-safe" approach where a failure in one provider (e.g., Lyrics) doesn't stop the rest of the metadata retrieval.
- **Performance (Concurrency):**
    - Default to parallel processing for large batches of files.
    - Optimize file I/O operations to minimize latency when writing large cover art or extensive tags.
- **Safety Protocol:** Adhere to the `--reserve` flag by default in critical operations to prevent accidental data loss of original files during testing or batch processing.
