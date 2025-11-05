# Aggie File Integrity Monitor

A lightweight, real-time file integrity monitoring tool that tracks changes to files and directories. This tool helps detect unauthorized modifications, additions, or deletions of files by maintaining a cryptographic baseline of your monitored directories.

## Features

- **Real-time Monitoring**: Continuously monitors specified directories for file changes
- **SHA-256 Hashing**: Uses cryptographic hashing to detect even the smallest file modifications
- **Change Detection**: Identifies three types of changes:
  - New files created
  - Existing files modified
  - Files deleted
- **Baseline Management**: Create and maintain baseline snapshots of known-good file states
- **Smart Exclusions**: Automatically excludes virtual environments, cache directories, and hidden folders
- **File Stabilization**: Waits for files to finish writing before calculating hashes to avoid false positives
- **Recursive Scanning**: Monitors all subdirectories within the specified path

## Installation

1. Clone this repository:
```bash
git clone https://github.com/Blu3Stone/Aggie-File-Integrity-Monitoring.git
cd Aggie-File-Integrity-Monitoring
```

2. Ensure you have Python 3.6+ installed:
```bash
python --version
```

3. No external dependencies required - uses only Python standard library

## Usage

Run the script:
```bash
python aggie_fim.py
```

### Menu Options

The tool presents an interactive menu with three options:

**1. Create new baseline**
- Scans the current directory and all subdirectories
- Generates SHA-256 hashes for all files
- Saves the baseline to `baseline.txt`
- Run this when your files are in a known-good state

**2. Start Monitoring**
- Loads the baseline file
- Continuously monitors for changes
- Alerts when files are added, modified, or deleted
- Press Ctrl+C to stop monitoring

**3. Exit**
- Closes the application

## Configuration

You can customize the following parameters in `aggie_fim.py`:

```python
MONITOR_DIR = '.'  # Directory to monitor (default: current directory)
BASELINE_FILE = 'baseline.txt'  # File storing baseline hashes
POLLING_INTERVAL = 0.2  # How often to check for changes (seconds)
STABILIZATION_DELAY = 0.1  # Wait time for file stabilization
STABILIZATION_RETRIES = 2  # Number of hash verification attempts
```

## Example Output

```
--- 🦅 AGGIE FILE INTEGRITY MONITOR ---
1) Create new baseline (Make sure directory is clean!)
2) Start Monitoring
3) Exit

Enter choice (1/2/3): 1
📝 Creating new baseline for directory: /path/to/monitor
✅ Baseline created in 'baseline.txt'. Wrote 42 files. Ready to monitor!

Enter choice (1/2/3): 2
👀 Monitoring started at 2024-11-05 10:30:00
   Baseline has 42 files
   (Press Ctrl+C to stop)
[2024-11-05 10:31:15] ⚠️  NEW FILE DETECTED: /path/to/monitor/newfile.txt
[2024-11-05 10:32:30] 🚨 FILE CHANGED: /path/to/monitor/document.pdf
[2024-11-05 10:33:45] 🗑️  FILE DELETED: /path/to/monitor/oldfile.txt
```

## How It Works

1. **Baseline Creation**: The tool walks through the directory tree and computes SHA-256 hashes for each file, storing them in a baseline file with the format `filepath|hash`

2. **Continuous Monitoring**: The monitoring loop periodically scans the directory and compares current file hashes against the baseline

3. **Change Detection**:
   - New files: Present in current scan but not in baseline
   - Modified files: Hash differs from baseline
   - Deleted files: Present in baseline but not in current scan

4. **Stabilization**: Before alerting on changes, the tool performs multiple hash calculations to ensure the file has finished being written

## Testing

Run the included test suite:
```bash
python test_aggie_fim.py
```

The test creates a temporary directory, sets up a baseline, and simulates file modifications, additions, and deletions to verify the monitoring functionality.

## Security Considerations

- The tool requires read access to all monitored files
- Baseline files contain file paths and hashes - protect them appropriately
- SHA-256 provides cryptographic-strength integrity verification
- Does not require elevated privileges unless monitoring protected directories
- Automatically skips files it cannot access due to permissions

## Use Cases

- **Development**: Monitor project directories for unexpected changes
- **Security**: Detect unauthorized file modifications
- **Compliance**: Maintain audit trails of file changes
- **System Administration**: Track configuration file changes
- **Data Integrity**: Verify critical files remain unmodified

## Limitations

- Does not preserve baseline across script restarts (baseline updates in memory)
- Cannot monitor files while they are locked by other processes
- File metadata changes (permissions, timestamps) are not tracked
- Not designed for monitoring extremely large directories (10,000+ files)

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.
