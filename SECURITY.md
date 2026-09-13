# Security Policy

Please do not open a public issue for a suspected vulnerability. Report it
privately through GitHub's **Report a vulnerability** feature on the Security
tab. Include reproduction steps, impact, and the affected version.

Only the latest released version is supported with security fixes.

The backend runs inside the Rust/Tauri process. It exposes a small set of typed
IPC commands to the local webview, with no HTTP listener or shell plugin. Rust
validates inputs and uses parameterized SQLite queries in the OS user-data
directory. The database is not encrypted; security depends on the OS user account
and filesystem permissions. Existing Python databases are backed up before the
native backend migrates them.
