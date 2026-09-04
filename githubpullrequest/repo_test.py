import os
import tempfile
import unittest
from types import SimpleNamespace

from . import repo
from .state import SESSION


def _view(file_name):
    return SimpleNamespace(file_name=lambda: file_name)


class RelPathTest(unittest.TestCase):
    def setUp(self):
        SESSION.reset()
        SESSION.root = os.sep + os.path.join("repo")

    def tearDown(self):
        SESSION.reset()

    def test_cases(self):
        root = SESSION.root
        cases = {
            "inside_the_repo": (os.path.join(root, "a.py"), "a.py"),
            "nested": (os.path.join(root, "pkg", "b.py"), "pkg/b.py"),
            "outside_the_repo": (os.sep + os.path.join("other", "c.py"), None),
            "no_file": (None, None),
        }

        for name, (file_name, expected) in cases.items():
            with self.subTest(name):
                self.assertEqual(repo.rel_path(_view(file_name)), expected)

    def test_no_root_loaded(self):
        SESSION.root = None

        self.assertIsNone(repo.rel_path(_view(os.sep + "repo" + os.sep + "a.py")))

    def test_abs_path_round_trips(self):
        absolute = repo.abs_path("pkg/b.py")

        self.assertEqual(absolute, os.path.join(SESSION.root, "pkg", "b.py"))
        self.assertEqual(repo.rel_path(_view(absolute)), "pkg/b.py")


@unittest.skipUnless(hasattr(os, "symlink"), "needs symlink support")
class SymlinkedRootTest(unittest.TestCase):
    """A checkout reached through a symlink: `git rev-parse --show-toplevel` answers
    with the resolved path, Sublime with the path the file was opened under."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        base = os.path.realpath(self._tmp.name)

        self.real_root = os.path.join(base, "real", "repo")
        os.makedirs(os.path.join(self.real_root, "pkg", "deep"))

        self.link_root = os.path.join(base, "link")
        os.symlink(os.path.join(base, "real"), self.link_root)
        self.link_root = os.path.join(self.link_root, "repo")

        SESSION.reset()

    def tearDown(self):
        SESSION.reset()
        self._tmp.cleanup()

    def test_unresolved_root_keeps_the_symlinked_prefix(self):
        inside = os.path.join(self.link_root, "pkg", "deep")

        self.assertEqual(repo._unresolved_root(inside, self.real_root), self.link_root)

    def test_unresolved_root_at_the_root_itself(self):
        self.assertEqual(
            repo._unresolved_root(self.link_root, self.real_root), self.link_root
        )

    def test_unresolved_root_falls_back_when_it_does_not_agree(self):
        outside = os.path.dirname(os.path.dirname(self.real_root))

        self.assertEqual(repo._unresolved_root(outside, self.real_root), self.real_root)

    def test_rel_path_matches_across_the_symlink(self):
        # Session loaded under the symlinked prefix, view opened under the real one.
        SESSION.root = self.link_root
        real_file = os.path.join(self.real_root, "pkg", "b.py")

        self.assertEqual(repo.rel_path(_view(real_file)), "pkg/b.py")

        # And the other way round.
        SESSION.root = self.real_root
        link_file = os.path.join(self.link_root, "pkg", "b.py")

        self.assertEqual(repo.rel_path(_view(link_file)), "pkg/b.py")

    def test_rel_path_still_rejects_a_foreign_file(self):
        SESSION.root = self.link_root
        outside = os.path.join(os.path.dirname(self.real_root), "elsewhere", "c.py")

        self.assertIsNone(repo.rel_path(_view(outside)))


class RunGitTest(unittest.TestCase):
    def test_read_only_command_succeeds(self):
        # `git --version` needs no repository and mutates nothing.
        rc, out = repo.run_git(os.getcwd(), ["--version"])

        self.assertEqual(rc, 0)
        self.assertIn("git version", out)

    def test_failure_returns_one_and_empty(self):
        rc, out = repo.run_git(os.getcwd(), ["definitely-not-a-git-command"])

        self.assertNotEqual(rc, 0)
        self.assertEqual(out, "")

    def test_git_root_outside_a_repo(self):
        self.assertIsNone(repo.git_root(os.sep))


if __name__ == "__main__":
    unittest.main()
