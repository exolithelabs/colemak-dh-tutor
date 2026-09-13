"""CI integration check against the actual PyInstaller executable, not Flask's test client."""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main():
    root = Path(__file__).resolve().parents[1]
    binaries = list((root / "src-tauri/binaries").glob("colemak-backend-*"))
    if len(binaries) != 1:
        raise RuntimeError("Expected exactly one bundled sidecar")
    token = secrets.token_urlsafe(32)
    with tempfile.TemporaryDirectory(prefix="colemak-smoke-") as directory:
        for launch in range(2):
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            process = subprocess.Popen(
                [str(binaries[0]), "--port", str(port), "--data-dir", directory],
                env={**os.environ, "COLEMAK_SIDECAR_TOKEN": token},
                cwd=directory,
            )
            def call(path, body=None, authenticate=True):
                headers = {"X-App-Token": token} if authenticate else {}
                if body is not None:
                    headers["Content-Type"] = "application/json"
                request = Request(f"http://127.0.0.1:{port}/api/{path}",
                                  data=json.dumps(body).encode() if body is not None else None,
                                  headers=headers)
                with urlopen(request, timeout=2) as response:
                    return json.load(response)
            try:
                deadline = time.monotonic() + 30
                while True:
                    if process.poll() is not None:
                        raise RuntimeError(f"Sidecar exited: {process.returncode}")
                    try:
                        call("health")
                        break
                    except (URLError, TimeoutError):
                        if time.monotonic() >= deadline:
                            raise RuntimeError("Sidecar failed to become ready")
                        time.sleep(0.2)
                try:
                    call("health", authenticate=False)
                    raise AssertionError("Unauthenticated API was accessible")
                except HTTPError as error:
                    assert error.code == 401
                assert len(call("lessons")) >= 20
                if launch == 0:
                    call("user/progress", {"username": "smoke", "lesson_id": 999, "wpm": 42, "accuracy": 97})
                progress = call("user/progress/smoke")
                assert len(progress) == 1 and progress[0]["wpm"] == 42
                assert (Path(directory) / "colemak.db").is_file()
            finally:
                if os.name == "nt":
                    # PyInstaller one-file executables have a bootloader child.
                    subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                   check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
    print("Packaged sidecar: startup, authentication, save, and restart persistence passed")


if __name__ == "__main__":
    main()
