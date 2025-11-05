import os
import hashlib
import time
import sys
from datetime import datetime

# --- CONFIGURATION ---
# The folder you want to monitor. '.' means the current folder the script is in.
# You can change this to a specific path like "C:/Users/Blu3stone/Documents/Sensitive"
MONITOR_DIR = '.' 

# The file where we store the "known good" hashes
BASELINE_FILE = 'baseline.txt'

# How often to check for changes (in seconds)
POLLING_INTERVAL = 0.2

# When a file appears to be new/changed, wait up to this many seconds
# (split across retries) for the file to settle before alerting.
STABILIZATION_DELAY = 0.1
STABILIZATION_RETRIES = 2

def calculate_file_hash(filepath):
    """
    Calculates the SHA-256 hash of a file.
    
    We read the file in chunks (4096 bytes) instead of loading the whole 
    thing into memory at once. This prevents the script from crashing 
    if it tries to hash a massive video file or ISO.
    """
    sha256_hash = hashlib.sha256()
    
    try:
        with open(filepath, "rb") as f:
            # Read the file in small chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (PermissionError, FileNotFoundError):
        # Sometimes purely temporary files disappear before we can hash them,
        # or we don't have admin permissions. We ignore those safely.
        return None


def stabilize_hash(filepath, retries=STABILIZATION_RETRIES, delay=STABILIZATION_DELAY):
    """
    Repeatedly hash a file a few times with a short delay to allow
    writers to finish. Returns the last successful hash or None.
    """
    last_hash = None
    for _ in range(retries):
        h = calculate_file_hash(filepath)
        if h is not None:
            # If this is the first successful hash, store it
            if last_hash is None:
                last_hash = h
            else:
                # If hash equals last_hash, we consider it stable
                if h == last_hash:
                    return h
                last_hash = h
        time.sleep(delay)
    return last_hash

def create_baseline():
    """
    Scans the directory and saves the initial state (filepath + hash) 
    to the baseline text file.
    """
    print(f"📝 Creating new baseline for directory: {os.path.abspath(MONITOR_DIR)}")
    
    # Overwrite existing baseline file if it exists
    file_count = 0
    with open(BASELINE_FILE, 'w') as f:
        # os.walk() recursively finds all files in all subfolders
        for root, dirs, files in os.walk(MONITOR_DIR):
            # EXCLUDE .venv, __pycache__, and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['.venv', '__pycache__']] # don't include env or pycache folders
            for file in files:
                filepath = os.path.abspath(os.path.join(root, file))

                # Don't hash the script itself or the baseline file!
                script_name = os.path.basename(__file__) if '__file__' in globals() else 'aggie_fim.py'
                if file == script_name or file == BASELINE_FILE:
                    continue

                # For baseline creation we take an immediate snapshot (no long stabilization)
                file_hash = calculate_file_hash(filepath)

                if file_hash:
                    # Format: filepath|hash
                    f.write(f"{filepath}|{file_hash}\n")
                    file_count += 1
                    
    print(f"✅ Baseline created in '{BASELINE_FILE}'. Wrote {file_count} files. Ready to monitor!")

def load_baseline():
    """
    Reads the baseline text file and loads it into a Python dictionary.
    Returns: dict { filepath: hash }
    """
    baseline = {}
    if not os.path.exists(BASELINE_FILE):
        return None

    with open(BASELINE_FILE, 'r') as f:
        for line in f:
            if '|' in line:
                filepath, file_hash = line.strip().split('|', 1)
                # Ensure keys are absolute paths for consistent comparisons
                if not os.path.isabs(filepath):
                    filepath = os.path.abspath(filepath)
                baseline[filepath] = file_hash
    return baseline

def start_monitoring():
    """
    The main loop. Constantly checks the current state of files against
    the baseline dictionary loaded in memory.
    """
    
    # 1. Load the baseline we created earlier
    baseline_hashes = load_baseline()
    
    if baseline_hashes is None:
        print("❌ Error: Baseline not found!")
        print("   Run 'Choice A' first to create a baseline.")
        return

    print(f"👀 Monitoring started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Baseline has {len(baseline_hashes)} files")
    print("   (Press Ctrl+C to stop)")
    sys.stdout.flush()

    try:
        poll_count = 0
        while True:
            time.sleep(POLLING_INTERVAL)
            poll_count += 1
            
            # Snapshot of the current files on disk
            current_files = {}

            # 2. Scan current files
            for root, dirs, files in os.walk(MONITOR_DIR):
                # EXCLUDE .venv, __pycache__, and hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['.venv', '__pycache__']]
                for file in files:
                    filepath = os.path.abspath(os.path.join(root, file))

                    # Skip our own files
                    script_name = os.path.basename(__file__) if '__file__' in globals() else 'aggie_fim.py'
                    if file == script_name or file == BASELINE_FILE:
                        continue

                    current_hash = stabilize_hash(filepath)
                    if current_hash:
                        current_files[filepath] = current_hash

            # 3. Compare Current vs Baseline
            
            # CHECK FOR NEW FILES or MODIFIED FILES
            for filepath, current_hash in current_files.items():
                # NEW FILE
                if filepath not in baseline_hashes:
                    print(f"[{datetime.now()}] ⚠️  NEW FILE DETECTED: {filepath}")
                    sys.stdout.flush()
                    # Add to baseline (use the stable hash)
                    baseline_hashes[filepath] = current_hash

                # MODIFIED
                elif baseline_hashes.get(filepath) != current_hash:
                    # Only alert if the current (stabilized) hash differs from baseline
                    print(f"[{datetime.now()}] 🚨 FILE CHANGED: {filepath}")
                    sys.stdout.flush()
                    # Update baseline so we don't spam the alert
                    baseline_hashes[filepath] = current_hash

            # CHECK FOR DELETED FILES
            # (If it's in baseline but NOT in current_files)
            for filepath in list(baseline_hashes.keys()):
                if filepath not in current_files and not os.path.exists(filepath):
                    print(f"[{datetime.now()}] 🗑️  FILE DELETED: {filepath}")
                    sys.stdout.flush()
                    del baseline_hashes[filepath]

    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user.")
        sys.stdout.flush()

def main():
    while True:
        print("\n--- 🦅 AGGIE FILE INTEGRITY MONITOR ---")
        print("1) Create new baseline (Make sure directory is clean!)")
        print("2) Start Monitoring")
        print("3) Exit")
        
        choice = input("\nEnter choice (1/2/3): ")
        
        if choice == '1':
            create_baseline()
        elif choice == '2':
            start_monitoring()
        elif choice == '3':
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()