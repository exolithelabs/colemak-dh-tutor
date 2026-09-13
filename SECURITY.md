# Security Policy

Please do not open a public issue for a suspected vulnerability. Report it
privately through GitHub's **Report a vulnerability** feature on the Security
tab. Include reproduction steps, impact, and the affected version.

Only the latest released version is supported with security fixes.

The Python service is an implementation detail of the desktop application. It
binds only to a randomly selected loopback port and requires a per-process
authentication token. It is not designed or supported as a network service.
