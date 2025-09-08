# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Repository overview
- Name: repo-scan-install
- Purpose: CLI to scan a JSON manifest of git repositories, report which are missing locally, and (optionally) clone them and run an install command per repo.
- Language/tooling: Python 3.9+, setuptools; console script entry point `repo-scan-install`.

Common commands
- Create a virtual environment (optional but recommended):
  - python3 -m venv .venv && source .venv/bin/activate
- Install for development (editable mode):
  - pip install -e .
- Build sdist/wheel (requires `build` package):
  - python -m pip install --upgrade build
  - python -m build
- Run the CLI (plan only by default):
  - cp repos.example.json repos.json
  - repo-scan-install --manifest repos.json --base-dir "$HOME/src"
- Apply actions (clone and optionally run install commands):
  - repo-scan-install --manifest repos.json --base-dir "$HOME/src" --apply --run-install
- Run from source (without console entry point):
  - python -m repo_scan_install.cli --manifest repos.json --base-dir "$HOME/src"
- Lint/tests: not configured in this repo yet (see Follow-up tasks).

High-level architecture
- Package: repo_scan_install (src layout)
  - cli.py
    - load_manifest(path): reads JSON, validates it has a top-level `repos` list.
    - is_git_repo(path): returns true if `.git/` exists in the target directory.
    - plan_actions(manifest, base_dir): returns a list of actions per repo entry:
      - noop: destination exists and is a git repo.
      - clone: destination missing or not a git repo; may also carry an `install` command list.
    - apply_actions(actions, run_install_flag, verbose): executes planned clones and, if requested, the per-repo `install` command list inside the repo directory. Tracks failures and prints status.
    - run(cmd, cwd, verbose): subprocess wrapper with optional echoing when `--verbose` is used.
    - main(argv): parses flags; resolves `base_dir` by precedence (CLI `--base-dir` > manifest `base_dir` > `$HOME/src`); prints the plan unless `--apply` is given; executes actions when applying.

Manifest contract (JSON)
- Top level keys:
  - base_dir (optional): default base directory; overridden by `--base-dir`.
  - repos (required): list of repo entries.
- Repo entry keys:
  - name (required)
  - url (required)
  - path (optional; defaults to `name`)
  - install (optional; list of strings, e.g., ["make", "install"]) — only runs when both `--apply` and `--run-install` are provided.

Behavior notes and gotchas
- Safe-by-default: without `--apply`, the CLI prints a plan and makes no changes.
- Install commands run only when both `--apply` and `--run-install` are set.
- If the destination directory exists but is not a git repo, `git clone` will likely fail; move or remove the directory before applying.
- All subprocess calls are synchronous and use the system `git`.
- Exit code is non-zero when applying if any action fails.

Important files
- README.md: Quick start and manifest format, mirrors the commands above.
- repos.example.json: Copy to `repos.json` as a starting point.
- pyproject.toml: setuptools config; defines console entry point `repo-scan-install` and Python >=3.9.
- No CLAUDE.md, Cursor rules, or Copilot instructions present at this time.

Follow-up tasks (to enable lint/tests explicitly)
1) Add pytest
   - pip install -U pytest
   - Create `tests/test_cli.py` with at least a help-smoke test that runs `python -m repo_scan_install.cli --help` and asserts exit code 0.
   - Run tests: pytest -q
   - Run a single test: pytest tests/test_cli.py::test_help -q
2) Add ruff and black
   - pip install -U ruff black
   - In pyproject.toml add minimal config:
     [tool.ruff]
     line-length = 100
     target-version = "py39"

     [tool.black]
     line-length = 100
     target-version = ["py39"]
   - Lint: ruff check .
   - Format: black .
3) Optional: pre-commit and CI
   - pip install -U pre-commit && pre-commit sample-config > .pre-commit-config.yaml && pre-commit install
   - Add a GitHub Actions workflow to run pytest and ruff on push/PR.

