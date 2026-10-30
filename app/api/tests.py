"""Run t() for unit files in app/api/k and app/api/f.

Usage, from anywhere:
    python app/api/tests.py                 # files edited since their last pass
    python app/api/tests.py --all           # every file
    python app/api/tests.py <file> [...]    # just these files
    python app/api/tests.py --watch         # keep running: test a file when it is saved,
                                                #   press  a  to run every file,  q  to quit

A content hash per file is kept in app/api/.tests_cache.json.
A file's hash is recorded only when its t() passes, so a failing or
skipped file stays scheduled until it passes.

A t() that needs a data store raises unittest.SkipTest when the store
is unavailable. Skips are reported separately from failures and do not
fail the run.

In watch mode every run happens in a subprocess so edited modules are
imported fresh.
"""

import hashlib
import importlib
import json
import select
import subprocess
import sys
import termios
import time
import traceback
import tty
from pathlib import Path
from unittest import SkipTest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
UNIT_DIRS = ("k", "f")
CACHE_PATH = HERE / ".tests_cache.json"
POLL_SECONDS = 0.5


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
        files.extend(p for p in sorted((HERE / sub).glob("*.py")) if p.name != "__init__.py")
    return files


def select_edited_files(files: list[Path], cache: dict[str, str]) -> list[Path]:
    return [p for p in files if cache.get(to_key(p)) != hash_file(p)]


def to_key(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def to_module_name(path: Path) -> str:
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def run_file_tests(path: Path) -> str:
    """Import the file and call its t(). Return "pass", "skip" or "fail"."""
    key = to_key(path)
    try:
        module = importlib.import_module(to_module_name(path))
        test = getattr(module, "t", None)
        if test is None:
            print(f"FAIL {key}: no t() defined")
            return "fail"
        test()
    except SkipTest as reason:
        print(f"SKIP {key}: {reason}")
        return "skip"
    except Exception:
        print(f"FAIL {key}")
        traceback.print_exc()
        return "fail"
    print(f"PASS {key}")
    return "pass"


def run_targets(targets: list[Path]) -> int:
    """Run t() for each target in this process, record passes, print a summary. Return the exit code."""
    if not targets:
        print("nothing to test: no files edited since their last pass")
        return 0
    cache = load_cache()
    counts = {"pass": 0, "skip": 0, "fail": 0}
    for path in targets:
        outcome = run_file_tests(path)
        counts[outcome] += 1
        if outcome == "pass":
            cache[to_key(path)] = hash_file(path)
    save_cache(cache)
    print(f"\n{counts['pass']} passed, {counts['skip']} skipped, {counts['fail']} failed")
    return 1 if counts["fail"] else 0


def run_in_subprocess(args: list[str]) -> None:
    """Run this script again with args in a fresh interpreter, streaming its output."""
    print(f"\n--- {time.strftime('%H:%M:%S')} {' '.join(args)} ---")
    subprocess.run([sys.executable, str(Path(__file__).resolve()), *args], cwd=ROOT)


def read_key() -> str | None:
    """Return one pending keypress, or None if none arrived within the poll interval."""
    ready, _, _ = select.select([sys.stdin], [], [], POLL_SECONDS)
    return sys.stdin.read(1) if ready else None


def watch() -> int:
    """Rerun a file's t() whenever it is saved; `a` runs every file, `q` quits."""
    seen = {p: hash_file(p) for p in find_unit_files()}
    print(f"watching {HERE.name}/{{{','.join(UNIT_DIRS)}}}  |  a: run all   q: quit")
    fd = sys.stdin.fileno()
    saved_tty = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        while True:
            key = read_key()
            if key == "q":
                break
            if key == "a":
                run_in_subprocess(["--all"])
                seen = {p: hash_file(p) for p in find_unit_files()}
                continue
            for path in find_unit_files():
                digest = hash_file(path)
                if seen.get(path) != digest:
                    seen[path] = digest
                    run_in_subprocess([to_key(path)])
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved_tty)
    return 0


def main(argv: list[str]) -> int:
    sys.path.insert(0, str(ROOT))
    if "--watch" in argv:
        return watch()

    files = find_unit_files()
    named = [Path(a) for a in argv if not a.startswith("--")]
    if named:
        targets = [(ROOT / p).resolve() if not p.is_absolute() else p for p in named]
    elif "--all" in argv:
        targets = files
    else:
        targets = select_edited_files(files, load_cache())
    return run_targets(targets)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
