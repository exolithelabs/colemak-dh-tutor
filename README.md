# Colemak-DH Tutor

A privacy-friendly desktop touch-typing tutor for the Colemak-DH keyboard
layout. It provides progressive lessons, real-time finger guidance, custom text
practice, and local progress history.

## Desktop architecture

- Vue 3 and TypeScript render the interface inside a Tauri v2 webview.
- Rust owns application lifecycle and launches the Python service as a bundled
  sidecar.
- The sidecar binds to a random loopback port and requires a new random token
  on every launch.
- Progress is stored in SQLite under the operating system's per-user app-data
  directory. No account or cloud service is used.
- Web content cannot invoke the shell plugin. Only the narrow Rust commands in
  `src-tauri/src/lib.rs` are exposed to the webview.

## User data

This repository and the installed application contain code and bundled assets
only. On first launch, Tauri creates a private data directory for the current OS
user and the backend creates `colemak.db` inside it. Each operating-system user
therefore gets independent progress data; uninstalling or upgrading the app does
not write data back into this repository.

Typical locations are:

- Windows: `%APPDATA%\\io.github.exolithelabs.ColemakDHTutor\\colemak.db`
- Linux: `$XDG_DATA_HOME/io.github.exolithelabs.ColemakDHTutor/colemak.db`, or
  `~/.local/share/io.github.exolithelabs.ColemakDHTutor/colemak.db`
- macOS: `~/Library/Application Support/io.github.exolithelabs.ColemakDHTutor/colemak.db`

The exact base directory is selected by the operating system through Tauri's
`app_data_dir` API. The Python backend requires this path at startup and has no
fallback that can create user data in the source or installation directory.

## Development

Prerequisites:

- Node.js 22 or newer
- Rust 1.84 or newer
- Python 3.11 or newer
- Tauri's platform prerequisites

Install and run on Windows:

```powershell
npm.cmd install
npm.cmd --prefix frontend install
python -m pip install -r backend/requirements-build.txt
npm.cmd run sidecar:windows
npm.cmd run tauri dev
```

On Linux, replace the sidecar command with:

```bash
./scripts/build-sidecar.sh
npm run tauri dev
```

## GitHub build and release workflow

All clean tests and distributable builds run in GitHub Actions. The
`desktop-build.yml` workflow runs for pull requests, pushes to `master`, version
tags, and manual dispatches. It produces:

- a Windows x86-64 NSIS `.exe` installer; and
- a Linux x86-64 Flatpak bundle plus an OSTree Flatpak repository archive.

Build artifacts are retained for 14 days. A tag such as `v0.1.0` also creates a
draft GitHub Release containing both platforms' files. Review and publish that
draft from GitHub. The workflow uses GitHub's automatic token and requires no
custom repository secrets while builds remain unsigned. Code signing is a
separate release decision; see `docs/RELEASING.md`.

## Keyboard shortcuts

- `Tab` focuses the typing input.
- `Escape` restarts the current lesson.

## License

Licensed under the [Apache License 2.0](LICENSE). See [NOTICE](NOTICE) for
attributions.
