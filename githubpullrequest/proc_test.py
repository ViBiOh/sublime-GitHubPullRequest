import subprocess
import unittest

from . import proc


class NoWindowKwargsTest(unittest.TestCase):
    def test_matches_platform(self):
        kwargs = proc.no_window_kwargs()
        if not hasattr(subprocess, "CREATE_NO_WINDOW"):
            self.assertEqual(kwargs, {})

            return

        self.assertEqual(kwargs["creationflags"], subprocess.CREATE_NO_WINDOW)
        self.assertTrue(kwargs["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW)
        self.assertEqual(kwargs["startupinfo"].wShowWindow, subprocess.SW_HIDE)

    def test_accepted_by_subprocess(self):
        proc.subprocess.run(
            ["python3", "-c", ""], capture_output=True, **proc.no_window_kwargs()
        )
