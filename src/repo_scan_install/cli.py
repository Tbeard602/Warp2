from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def load_manifest(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "repos" not in data or not isinstance(data["repos"], list):
        raise ValueError("Manifest must be a JSON object with a 'repos' list")
    return data


def is_git_repo(d: Path) -> bool:
    return (d / ".git").is_dir()


def clone_repo(url: str, dest: Path, verbose: bool = False) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", url, str(dest)]
    run(cmd, cwd=None, verbose=verbose)


def run_install(install_cmd: List[str], repo_dir: Path, verbose: bool = False) -> None:
    if not install_cmd:
        return
    if not isinstance(install_cmd, list) or not all(isinstance(x, str) for x in install_cmd):
        raise ValueError("install must be a list of strings, e.g. [\"make\", \"install\"]")
    run(install_cmd, cwd=repo_dir, verbose=verbose)


def run(cmd: List[str], cwd: Path | None, verbose: bool = False) -> None:
    if verbose:
        print(f"$ {' '.join(cmd)}" + (f"  (cwd={cwd})" if cwd else ""))
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def plan_actions(manifest: Dict[str, Any], base_dir: Path) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    for repo in manifest.get("repos", []):
        name = repo.get("name")
        url = repo.get("url")
        path = repo.get("path") or name
        install_cmd = repo.get("install") or []
        if not name or not url:
            print(f"Skipping invalid repo entry (missing name/url): {repo}")
            continue
        dest = base_dir / path
        if dest.exists() and is_git_repo(dest):
            actions.append({
                "type": "noop",
                "name": name,
                "dest": str(dest),
                "reason": "already present",
            })
        else:
            actions.append({
                "type": "clone",
                "name": name,
                "url": url,
                "dest": str(dest),
                "install": install_cmd,
            })
    return actions


def apply_actions(actions: List[Dict[str, Any]], run_install_flag: bool, verbose: bool = False) -> int:
    failures = 0
    for a in actions:
        t = a.get("type")
        if t == "noop":
            print(f"✔ {a['name']}: already present at {a['dest']}")
            continue
        if t == "clone":
            name = a["name"]
            url = a["url"]
            dest = Path(a["dest"])  # type: ignore[arg-type]
            try:
                print(f"→ Cloning {name} from {url} to {dest}")
                clone_repo(url, dest, verbose=verbose)
                if run_install_flag and a.get("install"):
                    print(f"→ Running install for {name}: {a['install']}")
                    run_install(a["install"], dest, verbose=verbose)  # type: ignore[arg-type]
                else:
                    if a.get("install"):
                        print(f"⚠ Install defined for {name} but --run-install not set; skipping")
            except subprocess.CalledProcessError as e:
                failures += 1
                print(f"✖ Failed action for {name}: {e}", file=sys.stderr)
            except Exception as e:  # noqa: BLE001
                failures += 1
                print(f"✖ Error for {name}: {e}", file=sys.stderr)
            continue
        print(f"? Unknown action type: {t}")
    return failures


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="repo-scan-install", description="Scan a manifest of git repositories and clone/install any that are missing.")
    p.add_argument("--manifest", default="repos.json", help="Path to manifest JSON (default: repos.json)")
    p.add_argument("--base-dir", default=None, help="Base directory for repo checkouts (overrides manifest base_dir)")
    p.add_argument("--apply", action="store_true", help="Apply actions; without this, prints a plan only")
    p.add_argument("--run-install", action="store_true", help="After cloning, run the repo's install command if defined")
    p.add_argument("--verbose", action="store_true", help="Print subprocess commands before running")

    args = p.parse_args(argv)

    manifest_path = Path(args.manifest)
    manifest = load_manifest(manifest_path)

    base_dir = Path(args.base_dir) if args.base_dir else Path(manifest.get("base_dir") or (Path.home() / "src"))
    base_dir = base_dir.expanduser().resolve()

    print(f"Base directory: {base_dir}")
    actions = plan_actions(manifest, base_dir)

    if not args.apply:
        print("Plan (no changes made):")
        for a in actions:
            if a["type"] == "noop":
                print(f"  - noop: {a['name']} already at {a['dest']}")
            elif a["type"] == "clone":
                install_msg = f", then install {a['install']}" if a.get("install") else ""
                print(f"  - clone: {a['name']} -> {a['dest']}{install_msg}")
        print("Use --apply to perform these actions.")
        if any(a.get("install") for a in actions) and not args.run_install:
            print("Hint: add --run-install to run install commands after cloning.")
        return 0

    failures = apply_actions(actions, run_install_flag=args.run_install, verbose=args.verbose)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

