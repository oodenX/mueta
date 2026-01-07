# Spec: Release v0.3.0 and Distribution Packages

## Overview
This track focuses on the official release of Mueta v0.3.0. The main goals are to tag the version, update project documentation, create a visual demo of the new AI features, and automate the creation of multi-platform distribution packages (RPM, DEB, EXE, DMG) via GitHub Releases.

## Functional Requirements
- **Version Tagging:** Create and push a `v0.3.0` Git tag to the remote repository.
- **Documentation Update:**
    - Update `README.md` to reflect v0.3.0 features (AI-powered Genre/Mood).
    - Add a "What's New in v0.3.0" section.
- **Visual Demo:** Create a new GIF demo (or update existing ones) specifically showcasing the `mueta analyze --semantic` and `mueta get-meta --semantic` commands.
- **CI/CD Pipeline Update:**
    - Refine the existing `.github/workflows/release.yml` to build and attach artifacts for Linux (RPM, DEB), Windows (EXE), and macOS (DMG).
    - Ensure build scripts for each platform are included in the repository.
- **GitHub Release:** Automatically generate a release on GitHub with release notes and all binary assets.

## Non-Functional Requirements
- **Release Integrity:** All binary artifacts must be verified for correct execution before final release.
- **Package Size Awareness:** Document the expected installation size (as previously estimated) in the release notes.

## Acceptance Criteria
- [ ] Git tag `v0.3.0` exists on GitHub.
- [ ] `README.md` contains updated information and a demo for v0.3.0.
- [ ] GitHub Release v0.3.0 contains:
    - `.deb` and `.rpm` files for Linux.
    - `.exe` for Windows.
    - `.dmg` for macOS.
    - Binary files for all platforms.
    - Build scripts used for generation.
- [ ] The release notes automatically summarize the changes from v0.2.0.

## Out of Scope
- Implementation of new features not already in the code.
- Publishing to PyPI (unless explicitly requested later).
