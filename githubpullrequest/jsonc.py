"""Reading Sublime's JSON-with-comments resource files (settings, menus, keymaps).

Only WHOLE-LINE `//` comments are stripped, which is all the packaged files use. A
trailing-comment stripper would have to understand string literals, or it would truncate
any value that legitimately contains `//`, a url being the obvious one."""

import json
import re
from typing import Any

_COMMENT_LINE_RE = re.compile(r"^\s*//.*$", re.MULTILINE)


def loads(text: str) -> Any:
    return json.loads(_COMMENT_LINE_RE.sub("", text))


def load_file(path: str) -> Any:
    with open(path, encoding="utf-8") as handle:
        return loads(handle.read())
