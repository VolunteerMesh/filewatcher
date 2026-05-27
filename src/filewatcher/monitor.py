import logging
import os
import shutil
import threading
import time
from collections import deque
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

LOG = logging.getLogger("filewatcher")


class _ChangeHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor

    def on_created(self, event):
        if not event.is_directory:
            self.monitor.record_event(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory:
            self.monitor.record_event(event.src_path, "modified")

    def on_moved(self, event):
        if not event.is_directory:
            self.monitor.record_event(event.dest_path, "moved")


class FileWatcherMonitor:
    """Monitor directories and keep backups of changed files. Detects bursts of file changes.

    Basic behavior:
    - Watch configured directories recursively.
    - On file create/modify/move, copy file to `backup_dir` preserving relative path.
    - Maintain a rolling window of events and if event rate crosses `burst_threshold`
      within `window_seconds`, log an alert and keep backing up.
    """

    def __init__(self, watch_dirs, backup_dir, interval=1.0, window_seconds=10, burst_threshold=50):
        self.watch_dirs = list(watch_dirs)
        self.backup_dir = backup_dir
        self.interval = interval
        self.window_seconds = window_seconds
        self.burst_threshold = burst_threshold

        self._observer = Observer()
        self._handler = _ChangeHandler(self)
        self._lock = threading.Lock()
        self._running = False

        # event timestamps per path (deque of timestamps)
        self._events = deque()
        self._last_alert = None

    def record_event(self, path, typ):
        ts = time.time()
        with self._lock:
            self._events.append(ts)
        LOG.debug("Event %s %s", typ, path)
        # perform backup immediately (best-effort)
        try:
            rel = self._relative_path(path)
            dest = os.path.join(self.backup_dir, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(path, dest)
            LOG.info("Backed up %s -> %s", path, dest)
        except Exception as e:
            LOG.warning("Failed to backup %s: %s", path, e)

    def _relative_path(self, path):
        # choose the first watch_dir that is a prefix
        for root in self.watch_dirs:
            if os.path.commonpath([os.path.abspath(root), os.path.abspath(path)]) == os.path.abspath(root):
                rel = os.path.relpath(path, root)
                return os.path.join(os.path.basename(root), rel)
        # fallback to basename
        return os.path.basename(path)

    def _check_burst(self):
        cutoff = time.time() - self.window_seconds
        with self._lock:
            while self._events and self._events[0] < cutoff:
                self._events.popleft()
            count = len(self._events)
        if count >= self.burst_threshold:
            now = time.time()
            if not self._last_alert or (now - self._last_alert) > self.window_seconds:
                LOG.warning("High event rate detected: %d events in %ds", count, self.window_seconds)
                self._last_alert = now
                return True
        return False

    def start(self):
        if self._running:
            return
        LOG.info("Starting FileWatcherMonitor: watch=%s backup=%s", self.watch_dirs, self.backup_dir)
        for d in self.watch_dirs:
            self._observer.schedule(self._handler, d, recursive=True)
        self._observer.start()
        self._running = True
        try:
            while self._running:
                burst = self._check_burst()
                if burst:
                    LOG.info("Burst handling: ensuring backups are up-to-date")
                time.sleep(self.interval)
        except KeyboardInterrupt:
            LOG.info("Interrupted")
        finally:
            self.stop()

    def stop(self):
        if not self._running:
            return
        self._running = False
        self._observer.stop()
        self._observer.join()
        LOG.info("Stopped monitor")


def sample_once(watch_dirs=None, backup_dir=None):
    # convenience helper for tests: return a simple dict
    return {
        "watch_dirs": watch_dirs or [],
        "backup_dir": backup_dir,
        "timestamp": datetime.utcnow().isoformat(),
    }
