"""Guards the package's entry-point surfaces against drifting apart: the command palette
(`Default.sublime-commands`), the menus (`Main.sublime-menu`, `Context.sublime-menu`) and
the key bindings (`Default.sublime-keymap`). All of them reference commands by string
only, so a renamed command leaves a dead entry with NO error: the item just does
nothing.

Stdlib only (no PyYAML/Sublime on the host), so `plugin.py` is scraped for its command
classes rather than imported (it imports `sublime`)."""

import ast
import os
import re
import unittest

from . import jsonc

_PACKAGE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MENU = os.path.join(_PACKAGE, "Main.sublime-menu")
_CONTEXT_MENU = os.path.join(_PACKAGE, "Context.sublime-menu")
_COMMANDS = os.path.join(_PACKAGE, "Default.sublime-commands")
_KEYMAP = os.path.join(_PACKAGE, "Default.sublime-keymap")
_REPOSITORY = os.path.join(_PACKAGE, "repository.json")
_PLUGIN = os.path.join(_PACKAGE, "plugin.py")

_COMMAND_CLASS_RE = re.compile(r"^class (GithubPullRequest\w*?)Command\b", re.MULTILINE)
_PACKAGES_PATH_RE = re.compile(r"\$\{packages\}/([^/]+)/")


def _snake_case(name):
    """Sublime's command id for a class name, e.g. GithubPullRequestLoad -> the
    palette's `github_pull_request_load`."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _plugin_command_ids():
    with open(_PLUGIN, encoding="utf-8") as handle:
        source = handle.read()

    return {_snake_case(name) for name in _COMMAND_CLASS_RE.findall(source)}


def _commands_defining_is_visible():
    """Command ids whose class declares `is_visible`. Parsed rather than imported, like
    the class names above."""
    with open(_PLUGIN, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())

    found = set()

    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue

        methods = {
            child.name for child in node.body if isinstance(child, ast.FunctionDef)
        }
        if "is_visible" in methods and node.name.endswith("Command"):
            found.add(_snake_case(node.name[: -len("Command")]))

    return found


def _menu_commands(items):
    """Every `command` reachable in a menu tree, submenus included."""
    found = set()

    for item in items:
        if "command" in item:
            found.add(item["command"])

        found.update(_menu_commands(item.get("children", [])))

    return found


def _package_name():
    repository = jsonc.load_file(_REPOSITORY)

    return repository["packages"][0]["name"]


class MenuTest(unittest.TestCase):
    def setUp(self):
        self.menu = jsonc.load_file(_MENU)
        self.menu_commands = _menu_commands(self.menu)

    def test_every_menu_command_is_implemented(self):
        for command in sorted(self.menu_commands):
            with self.subTest(command):
                if not command.startswith("github_pull_request"):
                    continue  # a Sublime built-in (edit_settings, open_file)

                self.assertIn(command, _plugin_command_ids())

    def test_every_palette_command_is_in_a_menu(self):
        # The menus are the discoverable surface: a command reachable only from the
        # palette is invisible to anyone who does not already know its name.
        palette = {entry["command"] for entry in jsonc.load_file(_COMMANDS)}

        self.assertEqual(palette - self.menu_commands, set())

    def test_every_key_bound_command_is_in_a_menu(self):
        # Sublime prints a command's key binding beside its menu entry, and that is the
        # only place a user can discover or customize one. A binding with no menu entry
        # is what Package Control flags.
        bound = {entry["command"] for entry in jsonc.load_file(_KEYMAP)}

        self.assertEqual(bound - self.menu_commands, set())

    def test_resource_paths_use_the_published_package_name(self):
        # `${packages}/<folder>/...` is resolved against the INSTALLED folder, which
        # Package Control names after repository.json. A stale literal points at a path
        # that does not exist, and the entry silently opens nothing. Both surfaces that
        # can carry one are checked: the menus, and the palette's `edit_settings` entry.
        referenced = set()

        for resource in (_MENU, _CONTEXT_MENU, _COMMANDS):
            with open(resource, encoding="utf-8") as handle:
                referenced.update(_PACKAGES_PATH_RE.findall(handle.read()))

        referenced.discard("User")  # the user's own config dir, not this package

        self.assertEqual(referenced, {_package_name()})


class ContextMenuTest(unittest.TestCase):
    def setUp(self):
        self.commands = _menu_commands(jsonc.load_file(_CONTEXT_MENU))

    def test_every_context_command_is_implemented(self):
        for command in sorted(self.commands):
            with self.subTest(command):
                self.assertIn(command, _plugin_command_ids())

    def test_every_context_command_hides_itself(self):
        # The context menu is shared by every buffer in every project, most of which have
        # nothing to do with a pull-request. Without `is_visible`, an entry sits there
        # (greyed out at best) in all of them, so a missing one is a real regression.
        visible = _commands_defining_is_visible()

        for command in sorted(self.commands):
            with self.subTest(command):
                self.assertIn(command, visible)

    def test_context_menu_has_no_separators(self):
        # Sublime does not drop a separator whose neighbours are all invisible, so one
        # here would draw a stray line in every buffer where the entries are hidden.
        for item in jsonc.load_file(_CONTEXT_MENU):
            self.assertNotEqual(item.get("caption"), "-")


class PaletteTest(unittest.TestCase):
    def test_captions_are_prefixed(self):
        # The palette is flat and unsorted by package, so the prefix is what groups
        # these entries together when the user types the package name. The settings
        # entry is the one exception: Sublime files every package's `edit_settings`
        # under `Preferences:`, so it groups with its peers there instead.
        for entry in jsonc.load_file(_COMMANDS):
            with self.subTest(entry["command"]):
                caption = entry["caption"]
                allowed = ("GitHubPullRequest: ", "Preferences: GitHubPullRequest ")

                self.assertTrue(
                    caption.startswith(allowed),
                    f"caption {caption!r} starts with none of {allowed}",
                )
