"""Run t() for every unit file in terrasim2/k and terrasim2/f that changed since it last passed.

Usage:
    python tests.py          # test files edited since their last pass
    python tests.py --all    # test every file regardless

A content hash per file is kept in .tests_cache.json at the repo root.
A file's hash is recorded only when its t() passes, so a failing file
stays scheduled until it is fixed.
"""

import hashlib
import importlib
import json
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE = "terrasim2"
UNIT_DIRS = ("k", "f")
CACHE_PATH = ROOT / ".tests_cache.json"


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    return json.loads(CACHE_PATH.read_text())


def save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True) + "\n")


def find_unit_files() -> list[Path]:
    files: list[Path] = []
    for sub in UNIT_DIRS:
        files.extend(p for p in sorted((ROOT / PACKAGE / sub).glob("*.py")) if p.name != "__init__.py")
    return files


def select_edited_files(files: list[Path], cache: dict[str, str]) -> list[Path]:
    return [p for p in files if cache.get(to_key(p)) != hash_file(p)]


def to_key(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def to_module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def run_file_tests(path: Path) -> bool:
    """Import the file and call its t(). Return True on pass."""
    key = to_key(path)
    try:
        module = importlib.import_module(to_module_name(path))
        test = getattr(module, "t", None)
        if test is None:
            print(f"FAIL {key}: no t() defined")
            return False
        test()
    except Exception:
        print(f"FAIL {key}")
        traceback.print_exc()
        return False
    print(f"PASS {key}")
    return True


def main(argv: list[str]) -> int:
    run_all = "--all" in argv
    sys.path.insert(0, str(ROOT))

    cache = load_cache()
    files = find_unit_files()
    targets = files if run_all else select_edited_files(files, cache)

    if not targets:
        print("nothing to test: no files edited since their last pass")
        return 0

    failed = 0
    for path in targets:
        if run_file_tests(path):
            cache[to_key(path)] = hash_file(path)
        else:
            failed += 1
    save_cache(cache)

    print(f"\n{len(targets) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
