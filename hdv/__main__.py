"""CLI entry point for hdv."""

from __future__ import annotations

import argparse
import io
import os
import sys
from pathlib import Path

from . import __version__
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
    parser.add_argument(
        "-s",
        "--string-column",
        dest="string_columns",
        action="append",
        default=None,
        metavar="COLUMN",
        help="Treat COLUMN as a regular string (disable path auto-detection for it); may be repeated",
    )
    parser.add_argument(
        "-c",
        "--columns",
        dest="columns",
        metavar="COL1,COL2,...",
        default=None,
        help="Comma-separated list of columns to show (in order); unlisted columns are hidden",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args()
    string_columns = args.string_columns or []
    column_filter = None
    if args.columns is not None:
        column_filter = [c.strip() for c in args.columns.split(",") if c.strip()]
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
        string_columns=string_columns,
        column_filter=column_filter,
        driver_class=driver_class,
    )
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
