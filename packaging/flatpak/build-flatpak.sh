#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ! -f "$1" ]]; then
  echo "Usage: $0 path/to/colemak-dh-tutor.deb" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
package_dir="$repo_root/packaging/flatpak"
input_dir="$package_dir/input"
build_dir="$repo_root/flatpak-build"
ostree_repo="$repo_root/flatpak-repo"
output_dir="$repo_root/dist"

mkdir -p "$input_dir" "$output_dir"
install -m644 "$1" "$input_dir/colemak-dh-tutor.deb"

flatpak-builder --force-clean --default-branch=stable --repo="$ostree_repo" "$build_dir" \
  "$package_dir/io.github.exolithelabs.ColemakDHTutor.yml"
flatpak build-update-repo --generate-static-deltas "$ostree_repo"
flatpak build-bundle "$ostree_repo" \
  --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo \
  "$output_dir/Colemak-DH-Tutor-x86_64.flatpak" \
  io.github.exolithelabs.ColemakDHTutor stable
tar -C "$repo_root" -czf "$output_dir/Colemak-DH-Tutor-flatpak-repo.tar.gz" flatpak-repo
