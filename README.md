# FileWatcher — File-change Monitor & Backup Service

`filewatcher` is a platform-friendly background agent designed to detect bursts of filesystem changes (useful as an early warning for mass-encryption activity) and keep best-effort backups of modified files.

Key features
- Watch configured directories recursively for file create/modify/move events
- Immediately copy changed files to a local backup store preserving directory layout
- Detect bursts of file activity and emit alerts in logs
- Optional Windows Service wrapper (via `pywin32`) to run as a native service

Requirements
- Python 3.8+
- See `requirements.txt` (includes `watchdog`, `psutil`; `pywin32` is Windows-only)

Quick Start (foreground)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
python -m filewatcher run -w C:\\ImportantData -b C:\\filewatcher_backups -i 2
```

Windows Service (optional)

- Install `pywin32` and use the `filewatcher.service.ServiceWrapper` to install the service. Running as a native Windows service requires administrator privileges.

Repository layout
- `src/filewatcher` — source package
- `tests` — unit tests
- `.github/workflows/ci.yml` — CI workflow (runs tests on Linux)
- `config.yaml.sample` — sample configuration for Windows

License: MIT
