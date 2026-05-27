import argparse
import logging
import os
import sys

from .monitor import FileWatcherMonitor, sample_once

LOG = logging.getLogger("filewatcher")


def status_cmd(args):
    print("FileWatcher service sample status:")
    print(sample_once(args.watch or [], args.backup))


def run_cmd(args):
    logging.basicConfig(level=logging.INFO)
    watch = args.watch or [os.getcwd()]
    backup = args.backup or os.path.join(os.getcwd(), "filewatcher_backup")
    monitor = FileWatcherMonitor(watch, backup, interval=args.interval, window_seconds=args.window, burst_threshold=args.threshold)
    monitor.start()


def build_parser():
    parser = argparse.ArgumentParser(prog="filewatcher", description="FileWatcher — simple file-change watchdog and backup agent")
    sub = parser.add_subparsers(dest="cmd")

    p_status = sub.add_parser("status", help="Show a brief status")
    p_status.add_argument("--watch", "-w", nargs="*", help="Directories being watched")
    p_status.add_argument("--backup", "-b", help="Backup directory")
    p_status.set_defaults(func=status_cmd)

    p_run = sub.add_parser("run", help="Run the monitor in foreground")
    p_run.add_argument("--watch", "-w", nargs="*", help="Directories to watch (default: cwd)")
    p_run.add_argument("--backup", "-b", help="Backup directory")
    p_run.add_argument("--interval", "-i", type=float, default=1.0, help="Main loop interval in seconds")
    p_run.add_argument("--window", type=int, default=10, help="Window seconds for burst detection")
    p_run.add_argument("--threshold", type=int, default=50, help="Event count threshold for burst")
    p_run.set_defaults(func=run_cmd)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
