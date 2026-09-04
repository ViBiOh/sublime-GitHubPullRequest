"""Repository access: read-only git plus repo-relative path mapping.

Only read-only git is ever run (`rev-parse`, `show`); the plugin never mutates git
state. No ``sublime`` import, so everything here is unit-testable."""

import os
import subprocess
from typing import List, Optional, Tuple

from .proc import no_window_kwargs
from .state import SESSION

_TIMEOUT = 5


def _unresolved_root(path: str, root: str) -> str:
    """`root` re-expressed under `path`'s own (possibly symlinked) prefix, or `root`
    itself when `path` does not sit under it once resolved.

    The re-expression is deliberately lexical: collapsing the `..` components is what
    preserves the symlinked prefix, which resolving would throw away. That is only
    correct while the components walked back over are real directories, so the result is
    checked against `root` and discarded when it does not agree."""
    inner = os.path.relpath(os.path.realpath(path), root)

    candidate = path
    if inner != os.curdir:
        candidate = os.path.join(path, *([os.pardir] * len(inner.split(os.sep))))

    candidate = os.path.normpath(candidate)

    if os.path.realpath(candidate) != os.path.realpath(root):
        return root

    return candidate


def git_root(path: str) -> Optional[str]:
    """Repository root containing `path`, or None when it is not inside a repo.

    Reported in `path`'s own terms, not git's. `git rev-parse --show-toplevel` resolves
    every symlink, while Sublime hands out the path a file was OPENED under, so a
    symlinked checkout (say ~/workspace -> ~/go/src/github.com/...) makes the two
    disagree: `rel_path` then walks out of the root with `..` and returns None for every
    view, which silently kills every per-view feature (no gutter icons, no popups, no
    thread ever matched to a buffer) even though the review loaded fine."""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=path,
            stderr=subprocess.STDOUT,
            timeout=_TIMEOUT,
            **no_window_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        return None

    return _unresolved_root(path, out.decode("utf-8").strip())


def run_git(root: str, args: List[str]) -> Tuple[int, str]:
    """(returncode, stdout) of a read-only git command run in `root`. Returns
    (1, "") on any failure, so callers only branch on the code."""
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
            **no_window_kwargs(),
        )
    except (OSError, subprocess.SubprocessError):
        return 1, ""

    return proc.returncode, proc.stdout


def rel_path(view) -> Optional[str]:
    """Repo-relative, forward-slash path for a view's file, or None when it has no
    file or sits outside the loaded repository. Duck-typed on ``view.file_name()``."""
    file_name = view.file_name()
    if not file_name or not SESSION.root:
        return None

    rel = os.path.relpath(file_name, SESSION.root)
    if rel.startswith(".."):
        # The view was opened through a different spelling of the same tree than the one
        # the session was loaded under (one side of a symlink, the other side of it).
        # Resolving both is the only way to tell that apart from a genuinely foreign
        # file, and it is worth the stat calls: getting it wrong drops the file out of
        # the review entirely.
        rel = os.path.relpath(
            os.path.realpath(file_name), os.path.realpath(SESSION.root)
        )
        if rel.startswith(".."):
            return None

    return rel.replace(os.sep, "/")


def abs_path(rel: str) -> str:
    return os.path.join(SESSION.root, rel.replace("/", os.sep))
