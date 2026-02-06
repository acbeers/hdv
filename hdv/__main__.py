"""CLI entry point for hdv."""

from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

from .app import HDVApp
from .driver import TTYInputDriver


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="hdv",
        description="Hierarchical Data Viewer - interactive drill-down for CSV files.",
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=lambda p: None if p is None else (Path(p) if p != "-" else "-"),
        default=None,
        help="Path to the CSV file, or '-' to read from stdin",
    )
    parser.add_argument(
        "-p",
        "--path-column",
        dest="path_column",
        metavar="COLUMN",
        default=None,
        help="Treat COLUMN as a slash-separated path and drill by path segments",
    )
    args = parser.parse_args()
    csv_path = args.csv_path

    use_stdin = False
    if csv_path is None:
        if sys.stdin.isatty():
            print("Error: no CSV file given (use a path, '-' for stdin, or pipe data)", file=sys.stderr)
            return 1
        source = io.StringIO(sys.stdin.read())
        source_name = "<stdin>"
        use_stdin = True
    elif csv_path == "-":
        source = io.StringIO(sys.stdin.read())
        source_name = "<stdin>"
        use_stdin = True
    else:
        if not csv_path.exists():
            print(f"Error: file not found: {csv_path}", file=sys.stderr)
            return 1
        if not csv_path.is_file():
            print(f"Error: not a file: {csv_path}", file=sys.stderr)
            return 1
        source = csv_path
        source_name = None

    # Use /dev/tty for input when stdin was used for CSV (Unix only)
    driver_class = (
        TTYInputDriver if (use_stdin and os.name != "nt") else None
    )
    app = HDVApp(
        source,
        source_name=source_name,
        path_column=args.path_column,
        driver_class=driver_class,
    )
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
