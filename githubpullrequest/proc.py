"""Console-window suppression for subprocess calls.

Sublime Text is a GUI process, so on Windows spawning a console program (git, gh,
tmux, codeowners) flashes a console window. Every subprocess call in this package
passes these kwargs. No ``sublime`` import, so it stays unit-testable."""

import subprocess
from typing import Any, Dict


def no_window_kwargs() -> Dict[str, Any]:
    """Extra subprocess kwargs that keep the child's console window hidden. Empty on
    POSIX, where CREATE_NO_WINDOW does not exist and there is no window to hide."""
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if not creationflags:
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    return {"creationflags": creationflags, "startupinfo": startupinfo}
