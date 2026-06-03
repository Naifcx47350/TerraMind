"""
Start TerraMind local dev stack (3 services) from one command.

Usage (from <repo-root>):
    conda activate terramind
    python run_dev.py

Opens:
    - Model API  http://localhost:8001
    - FrontPage  http://localhost:8000
    - React UI   http://localhost:3000

Press Ctrl+C to stop all services.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTPAGE = ROOT / "FrontPage"
FRONTEND = FRONTPAGE / "frontend-react"

PROCS: list[subprocess.Popen] = []


def _spawn(cmd: list[str], cwd: Path, *, shell: bool = False) -> subprocess.Popen:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    return subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        shell=shell,
    )


def _npm_cmd() -> list[str]:
    if sys.platform == "win32":
        return ["cmd", "/c", "npm", "run", "dev"]
    return ["npm", "run", "dev"]


def _stop_all() -> None:
    for p in PROCS:
        if p.poll() is None:
            p.terminate()
    deadline = time.time() + 8
    for p in PROCS:
        if p.poll() is not None:
            continue
        remaining = max(0, deadline - time.time())
        try:
            p.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            p.kill()
    PROCS.clear()


def _on_signal(signum, frame) -> None:
    print("\n[run_dev] Shutting down...")
    _stop_all()
    sys.exit(0)


def main() -> int:
    if not FRONTEND.joinpath("package.json").is_file():
        print(f"[run_dev] Missing {FRONTEND / 'package.json'} — run npm install there first.")
        return 1

    signal.signal(signal.SIGINT, _on_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _on_signal)

    print("[run_dev] Starting TerraMind (3 services)...")
    print(f"  repo: {ROOT}\n")

    try:
        PROCS.append(
            _spawn(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "terramind.api.app:app",
                    "--reload",
                    "--port",
                    "8001",
                ],
                ROOT,
            )
        )
        PROCS.append(
            _spawn(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--reload",
                    "--port",
                    "8000",
                ],
                FRONTPAGE,
            )
        )
        PROCS.append(_spawn(_npm_cmd(), FRONTEND, shell=sys.platform == "win32"))

        print("[run_dev] Model API  → http://localhost:8001  (terramind.api.app)")
        print("[run_dev] FrontPage  → http://localhost:8000  (app.main)")
        print("[run_dev] React UI   → http://localhost:3000  (npm run dev)")
        print("\n[run_dev] Open http://localhost:3000 in your browser.")
        print("[run_dev] Press Ctrl+C to stop all.\n")

        while True:
            for i, p in enumerate(PROCS):
                if p.poll() is not None:
                    names = ["Model API (8001)", "FrontPage (8000)", "React UI (3000)"]
                    print(f"[run_dev] {names[i]} exited with code {p.returncode}. Stopping others.")
                    _stop_all()
                    return p.returncode or 1
            time.sleep(0.5)

    except KeyboardInterrupt:
        _on_signal(None, None)
    except FileNotFoundError as e:
        print(f"[run_dev] Command not found: {e}")
        print("  Ensure Python, uvicorn, and npm are on PATH (conda + nvm).")
        _stop_all()
        return 1
    except Exception as e:
        print(f"[run_dev] Failed: {e}")
        _stop_all()
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
