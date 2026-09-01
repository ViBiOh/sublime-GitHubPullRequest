# Contributing to GitHubPullRequest

First off, thank you for considering contributing to GitHubPullRequest. It's people like you that make it such a great tool.

Following these guidelines helps to communicate that you respect the time of the people managing and developing this open source project. In return, they should reciprocate that respect in addressing your issue, assessing changes, and helping you finalize your pull requests.

There are many ways to contribute: improving the documentation, submitting bug reports and feature requests, or writing code which can be incorporated into GitHubPullRequest itself.

## Ground Rules

- Open an issue for any major change or enhancement you wish to make, and discuss it before writing code.
- Keep pull requests as small as possible, preferably one feature or fix per pull request.
- Every change must keep the plugin working on the platforms Sublime Text supports: Windows, macOS, and Linux. Continuous integration only runs on Linux, so anything platform sensitive (paths, subprocess invocation, line endings) needs manual thought.
- Be welcoming to newcomers and encourage diverse new contributors from all backgrounds.

## Your First Contribution

Working on your first pull request? You can learn how from this _free_ series, [How to Contribute to an Open Source Project on GitHub](https://egghead.io/series/how-to-contribute-to-an-open-source-project-on-github).

Feel free to ask for help; everyone is a beginner at first :smile_cat:

If a maintainer asks you to "rebase" your pull request, they're saying that a lot of code has changed and that you need to update your branch so it's easier to merge.

## Development Setup

You need:

- **Sublime Text 4** (build 4205 or later) to exercise the plugin itself.
- **Python 3** to run the tests and the linter. Note that the Sublime Text plugin host runs **Python 3.8**, so the code must stay 3.8 compatible even though the tests run on a newer interpreter. The only thing enforcing this is `target-version = "py38"` in `ruff.toml`; a green test run does not prove host compatibility.
- **[`ruff`](https://docs.astral.sh/ruff/)** for linting and formatting.
- **[`gh`](https://cli.github.com/)**, installed and authenticated, plus `git`, to try your change against a real pull request.

Install the package by symlinking the repository into your Sublime `Packages/` folder; see the Install section of the [README](README.md).

## Checks

Run all three before opening a pull request. Continuous integration runs exactly these.

```sh
python3 -m unittest discover -p '*_test.py'
ruff check . && ruff format .
python3 -m py_compile plugin.py githubpullrequest/anchors.py
```

The last one is a syntax check only: `plugin.py` and `githubpullrequest/anchors.py` are the two modules that import `sublime`, so they cannot run outside the editor. Verify them by loading the package in Sublime Text and driving a real pull request.

## Code Guidelines

Read [AGENTS.md](AGENTS.md) for the architecture tour and [DESIGN.md](DESIGN.md) for the interface contracts. The rules that will get a pull request rejected if broken:

- **Never mutate git state.** Only read-only git is allowed (`git show`, `git merge-base`, `git rev-parse`). No checkout, branch, reset, add, or commit, neither at runtime nor in tests.
- **All GitHub access goes through the `gh` CLI** as a subprocess. Never read the token, never use `requests` or `urllib` for GitHub.
- **Stay Python 3.8 safe.** No `X | Y` unions, no builtin generics in annotations (use `typing.List`, `Optional`, `Dict`, `Tuple`), no `match`, no `str.removeprefix`. Standard library only.
- **New code goes in the `githubpullrequest/` subpackage.** `plugin.py` is the only root-level module, because Sublime Text loads every root-level `.py` as an independent plugin. Only `plugin.py` and `githubpullrequest/anchors.py` may import `sublime`; keeping the rest free of it is what makes the code testable headlessly.

## Tests

- Files are named `*_test.py` and live next to the module they cover, in the same package.
- Use `unittest` with dictionary-keyed table cases (`cases = {"name": (...)}`) driven through `subTest`.
- Never hit the network or a real repository: inject a mock runner for `gh` and git calls.
- Any change to a pure module needs a test. Changes to the two `sublime` importing modules need a manual verification note in the pull request instead.

## Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

## How to Report a Bug

If you find a security vulnerability, do **not** open an issue. Email GitHubPullRequest@vibioh.fr instead.

The parts of this plugin worth reporting privately are:

- Anything that lets content coming from a pull request escape its sandbox. Comment bodies and their rendered HTML are written by anyone who can comment on the pull request, and they pass through three gates: the tag whitelist in `render.html_to_minihtml`, the `http(s)` only `href` check in `render._safe_anchor`, and the external-link check in `plugin._open_external`. A body that manages to trigger a plugin action (discard, resolve, edit) or reach a non `http(s)` handler is a vulnerability.
- Anything that exposes the `gh` authentication token, or that causes the plugin to run a mutating git or `gh` command.
- Anything that executes code or a shell command derived from remote data.

If you are unsure whether what you found qualifies, email rather than open an issue.

For anything else, open an issue with the Sublime Text build, your operating system, your `gh --version`, and the steps to reproduce.

## How to Suggest a Feature or Enhancement

If you find yourself wishing for a feature that doesn't exist, you are probably not alone. Open an issue describing the feature you would like to see, why you need it, and how it should work. The "Known limitations" section of the [README](README.md) and the deferred list at the end of [AGENTS.md](AGENTS.md) already track several ideas, and those are good places to start.

## Code Review Process

This project is maintained by a single person, so reviews happen when time allows rather than on a schedule. Pull requests that come with tests and a green set of checks move fastest.

After feedback has been given we expect responses within two weeks. After two weeks we may close the pull request if it isn't showing any activity.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE) that covers this project. There is no separate contributor license agreement.
