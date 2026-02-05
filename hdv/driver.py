"""Custom driver that reads input from /dev/tty when stdin is used for CSV data."""

from __future__ import annotations

from textual.drivers.linux_driver import LinuxDriver


class TTYInputDriver(LinuxDriver):
    """Linux driver that reads keyboard input from /dev/tty instead of stdin.

    Use this when stdin has been consumed for piped data (e.g. CSV from a pipe)
    so that key events come from the controlling terminal.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._tty_file = open("/dev/tty", "rb")
        self.fileno = self._tty_file.fileno()
        self.input_tty = True

    def close(self) -> None:
        if getattr(self, "_tty_file", None) is not None:
            try:
                self._tty_file.close()
            except OSError:
                pass
            self._tty_file = None
        super().close()
