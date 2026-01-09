import os
import shutil
import subprocess
import glob
from pathlib import Path
import random
import time

# Configuration
TEST_AUDIO_SOURCE = Path("/home/taurus/test/test_audio")
TEST_WORK_DIR = Path("/home/taurus/test/mueta_test_work")
ANALYZE_DIR = TEST_WORK_DIR / "analyze_test"
OUTPUT_AUDIO_DIR = Path(os.path.expanduser("~/.mueta/audio"))
OUTPUT_LYRICS_DIR = Path(os.path.expanduser("~/.mueta/lyrics"))

def setup_dirs():
    """Setup working directories."""
    print(f"[*] Setting up directories...")
    if TEST_WORK_DIR.exists():
        shutil.rmtree(TEST_WORK_DIR)
    TEST_WORK_DIR.mkdir(parents=True, exist_ok=True)
    ANALYZE_DIR.mkdir(parents=True, exist_ok=True)

    # Clean output dirs to ensure fresh run results
    # NOTE: Be careful not to delete user's actual data if they have it.
    # Since this is a test environment request, I will assume it's safe or I should check.
    # Actually, let's NOT delete the default ~/.mueta dirs blindly, but relying on unique filenames or checking timestamps might be better.
    # However, for the purpose of this specific test run, the user asked to test functionality.
    # I will just ensure the analyze dir is fresh.

    print(f"[*] Copying test files to {ANALYZE_DIR} for destructive testing...")
    # Copy all files for analyze test
    for f in TEST_AUDIO_SOURCE.glob("*"):
        if f.is_file():
            shutil.copy2(f, ANALYZE_DIR)
    print(f"[*] Copied {len(list(ANALYZE_DIR.glob('*')))} files.")

def run_command(cmd, shell=False):
    """Run a command and print output."""
    print(f"\n[CMD] {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            shell=shell
        )
        if result.returncode != 0:
            print(f"[FAIL] Return code: {result.returncode}")
            print(f"[STDERR]\n{result.stderr}")
        else:
            print(f"[OK] Return code: 0")
        return result
    except Exception as e:
        print(f"[ERROR] Execution failed: {e}")
        return None

def test_view_meta():
    print(f"\n{'='*50}\nTEST: view-meta\n{'='*50}")
    # Pick a random file from original source
    files = list(TEST_AUDIO_SOURCE.glob("*"))
    if not files:
        print("[SKIP] No files found.")
        return

    target = files[0] # Just pick first one for consistency
    run_command(["mueta", "view-meta", str(target)])

    # Test with cover
    print("\n[-] Testing with --show-cover (this might be messy in logs but verifies flag)")
    run_command(["mueta", "view-meta", "-c", str(target)])

def test_analyze():
    print(f"\n{'='*50}\nTEST: analyze (Destructive/In-Place)\n{'='*50}")
    # Run on the copy in ANALYZE_DIR
    target_dir = ANALYZE_DIR

    print("[-] Running analyze with default settings (BPM/Key + Semantic)...")
    CMD = ["mueta", "analyze", "-r", str(target_dir)]
    res = run_command(CMD)

    if res and res.returncode == 0:
        print("[+] Check if tags were written...")
        # Check one file
        sample = list(target_dir.glob("*"))[0]
        run_command(["mueta", "view-meta", str(sample)])

def test_get_meta_single():
    print(f"\n{'='*50}\nTEST: get-meta (Single File)\n{'='*50}")
    files = list(TEST_AUDIO_SOURCE.glob("*"))
    if len(files) < 2:
        return

    # Case 1: Reserve + Lyrics + Cover + Interactive (simulated or just dry run? Interactive is hard to automate)
    # We skip interactive for automation unless we use pexpect. We use -w 1 instead if needed.
    # Let's test non-interactive heavy flags.

    target = files[0]
    print(f"[-] Processing {target.name} with -r -l -c -e -a -s")
    CMD = [
        "mueta", "get-meta",
        "-r",           # Reserve original
        "-l",           # Download lyrics
        "-e",           # Embed lyrics
        "-c",           # Embed cover
        "-a",           # Analyze BPM/Key
        "--semantic",   # Semantic
        str(target)
    ]
    run_command(CMD)

def test_get_meta_folder():
    print(f"\n{'='*50}\nTEST: get-meta-from-folder\n{'='*50}")
    # We will use the REST of the files in TEST_AUDIO_SOURCE?
    # Or just run on the whole folder. Since we use -r, it's safe.

    print("[-] Running folder processing on entire source dir (preserved with -r)...")
    CMD = [
        "mueta", "get-meta-from-folder",
        "-r",
        "-w", "12",     # High concurrency
        "-l", "-c", "-e",
        "-a", "--semantic",
        str(TEST_AUDIO_SOURCE)
    ]
    run_command(CMD)

def verify_outputs():
    print(f"\n{'='*50}\nVERIFICATION\n{'='*50}")

    # 1. Check Output Audio Dir
    if not OUTPUT_AUDIO_DIR.exists():
        print(f"[FAIL] Output directory {OUTPUT_AUDIO_DIR} does not exist.")
        return

    out_files = list(OUTPUT_AUDIO_DIR.glob("*"))
    print(f"[*] Found {len(out_files)} files in output directory.")

    # 2. Check Lyrics Dir
    if not OUTPUT_LYRICS_DIR.exists():
        print(f"[WARN] Lyrics directory {OUTPUT_LYRICS_DIR} does not exist (maybe none found).")
    else:
        lrc_files = list(OUTPUT_LYRICS_DIR.glob("*.lrc"))
        print(f"[*] Found {len(lrc_files)} .lrc files.")

    # 3. Deep check of a few files using mutagen if possible or just mueta view-meta
    if out_files:
        sample = out_files[0]
        print(f"\n[-] Verifying processed file: {sample.name}")
        run_command(["mueta", "view-meta", str(sample)])

if __name__ == "__main__":
    setup_dirs()

    test_view_meta()
    test_analyze()
    test_get_meta_single()
    test_get_meta_folder()

    verify_outputs()
