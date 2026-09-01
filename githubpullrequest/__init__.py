"""Shared code for the GitHubPullRequest plugin.

Sublime Text imports every root-level .py of a package as an independent plugin, so
anything shared has to live below the root: a root module importing another root module
gets a second, separately-reloaded copy of its state. Only `plugin.py` stays at the root;
everything it builds on is a submodule here."""
