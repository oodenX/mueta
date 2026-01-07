# Plan: Release v0.3.0 and Distribution Packages

## Phase 1: Documentation and Demos
- [x] Task: Update `README.md` with v0.3.0 features and usage instructions for `--semantic`. eccca55
- [x] Task: Create a new demo GIF `demo/semantic.gif` showing the AI analysis in action. eccca55
- [x] Task: Add "What's New in v0.3.0" section to `README.md`. eccca55
- [ ] Task: Conductor - User Manual Verification 'Documentation and Demos' (Protocol in workflow.md)

## Phase 2: Build Scripts and CI/CD
- [ ] Task: Create/Update build scripts for Linux (PyInstaller + FPM for .deb/.rpm).
- [ ] Task: Create/Update build scripts for Windows (PyInstaller + Inno Setup or simple .exe).
- [ ] Task: Create/Update build scripts for macOS (PyInstaller + create-dmg).
- [ ] Task: Update `.github/workflows/release.yml` to trigger on `v*` tag and execute platform-specific builds.
- [ ] Task: Conductor - User Manual Verification 'Build Scripts and CI/CD' (Protocol in workflow.md)

## Phase 3: Tagging and Release
- [ ] Task: Commit all changes and push to `develop`.
- [ ] Task: Merge `develop` into `main` (if applicable) or prepare release branch.
- [ ] Task: Create and push `v0.3.0` tag.
- [ ] Task: Conductor - User Manual Verification 'Tagging and Release' (Protocol in workflow.md)
