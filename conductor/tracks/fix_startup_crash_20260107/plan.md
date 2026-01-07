# Plan: Fix Startup Crash on Fresh Install (v0.3.1)

## Phase 1: Fix Configuration Loading
- [x] Task: Update `src/mueta/core/config.py` to set default values for required fields (`audio_save_dir`, `lyrics_save_dir`, `acoustid_api_key`) to allow instantiation without a file. 1861941
- [ ] Task: Conductor - User Manual Verification 'Fix Configuration Loading' (Protocol in workflow.md)

## Phase 2: Verification
- [x] Task: Create a reproduction script/test that runs the app without a config file. 1861941
- [x] Task: Verify `mueta init` works as expected. 8f88aab
- [ ] Task: Conductor - User Manual Verification 'Verification' (Protocol in workflow.md)
