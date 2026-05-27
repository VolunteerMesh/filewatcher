import logging
import os
import sys

LOG = logging.getLogger("filewatcher.service")

# Windows service wrapper — optional, only imported on Windows with pywin32
try:
    import win32serviceutil
    import win32service
    import win32event
except Exception:
    win32serviceutil = None


class ServiceWrapper:
    def __init__(self, monitor_factory):
        self.monitor_factory = monitor_factory

    def run_as_service(self):
        if win32serviceutil is None:
            LOG.error("pywin32 not available: cannot install/run as Windows service on this platform")
            raise RuntimeError("pywin32 not available")

        class _Svc(win32serviceutil.ServiceFramework):
            _svc_name_ = "FileWatcherService"
            _svc_display_name_ = "FileWatcher File Monitor Service"

            def __init__(self, args):
                win32serviceutil.ServiceFramework.__init__(self, args)
                self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
                self.monitor = None

            def SvcStop(self):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                if self.monitor:
                    self.monitor.stop()
                win32event.SetEvent(self.hWaitStop)

            def SvcDoRun(self):
                import servicemanager
                LOG.info("Service starting")
                # create monitor from factory
                self.monitor = self.monitor_factory()
                try:
                    self.monitor.start()
                except Exception as e:
                    LOG.exception("Service failed: %s", e)
                    raise

        win32serviceutil.HandleCommandLine(_Svc)


def example_factory():
    # simple example to construct a monitor when running as service
    from .monitor import FileWatcherMonitor
    watch = [os.getcwd()]
    backup = os.path.join(os.getcwd(), "filewatcher_backup")
    return FileWatcherMonitor(watch, backup)


if __name__ == "__main__":
    # manual service helper
    sw = ServiceWrapper(example_factory)
    if win32serviceutil is None:
        print("pywin32 not installed — cannot run as native service. Use `run` to start in foreground.")
    else:
        sw.run_as_service()
