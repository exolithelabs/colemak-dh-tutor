#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
target_triple="$(rustc --print host-tuple)"

cd "$repo_root/backend"
python -m PyInstaller --clean --noconfirm colemak-backend.spec
install -Dm755 "dist/colemak-backend" "$repo_root/src-tauri/binaries/colemak-backend-$target_triple"
echo "Sidecar ready: src-tauri/binaries/colemak-backend-$target_triple"
