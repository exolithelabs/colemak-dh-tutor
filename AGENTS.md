# Project workflow

- Use this machine for source editing and read-only inspection. Run application
  tests, dependency audits, and production builds through GitHub Actions.
- Commit and push completed changes to GitHub as part of delivery, then inspect
  the matching workflow run and resolve failures caused by the changes.
- Do not publish or move version tags unless a release is requested. Existing
  published assets must not be overwritten.
- Keep user data, secrets, dependencies, and generated packages out of Git.
- Preserve installed-user data across upgrades; development data belongs in its
  separate development directory. Back up legacy schemas before changing them.
- Update README.md when user-visible behavior or the release workflow changes.
