# repo-scan-install

Scan for uninstalled git repositories from a manifest and install them.

This CLI reads a JSON manifest listing git repositories, checks if they exist locally, and for any that are missing it can clone them and optionally run install commands per repo.

Status: early scaffold. Safe-by-default (plan only); use --apply to execute.

## Quick start

1. Create and activate a virtual environment (optional but recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install the package in editable mode:

```bash
pip install -e .
```

3. Copy the sample manifest and edit it:

```bash
cp repos.example.json repos.json
$EDITOR repos.json
```

4. Plan actions (no changes made):

```bash
repo-scan-install --manifest repos.json --base-dir "$HOME/src"
```

5. Apply actions (clone missing repos; optionally run install steps):

```bash
repo-scan-install --manifest repos.json --base-dir "$HOME/src" --apply --run-install
```

## Manifest format (JSON)

```json
{
  "base_dir": "/home/you/src",
  "repos": [
    {
      "name": "example",
      "url": "https://github.com/user/example.git",
      "path": "example",  
      "install": ["make", "install"]
    }
  ]
}
```

- base_dir: optional; can be overridden by the --base-dir flag.
- repos[].path: optional; if omitted, defaults to repos[].name.
- repos[].install: optional; a list representing the command and its args to run inside the repo directory after cloning.

## Notes
- By default it prints a plan only. Add --apply to perform the actions.
- Install commands only run when both --apply and --run-install are provided.
- Requires: git, Python 3.9+.

