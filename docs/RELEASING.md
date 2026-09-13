# Releasing

## What CI produces

The **Desktop build** workflow runs on pull requests, pushes to `master`, version
tags, and manual dispatches. It produces:

- an unsigned Windows NSIS `.exe` installer;
- a Linux `.flatpak` bundle for direct testing; and
- `Colemak-DH-Tutor-flatpak-repo.tar.gz`, an OSTree repository ready to upload
  to your static Flatpak host.

Ordinary builds retain these as workflow artifacts for 14 days. Pushing a
version tag publishes a GitHub prerelease and attaches the packaged
applications. This uses the automatic per-run `GITHUB_TOKEN`; no personal access
token or custom secret is required.

Before packaging, CI validates matching application versions, runs frontend
regression tests, and audits Python and JavaScript dependencies. Both platform
jobs run backend regression tests and launch the frozen Python executable to
verify authentication, saving, and persistence across restart. Published assets
include a `SHA256SUMS` file. An already published release cannot be overwritten
by rerunning the workflow; create a new version instead.

## Creating a release candidate

Ensure the version matches in `package.json`, `src-tauri/Cargo.toml`,
`src-tauri/tauri.conf.json`, and the Flatpak metainfo, then push the commit and a
matching version tag:

```bash
git tag v0.1.0
git push origin master v0.1.0
```

After both platform jobs pass, the workflow publishes the prerelease with its
downloadable assets. Install-test these unsigned builds before promoting them
to a stable release.

## Before the first public release

1. Review and install both CI artifacts on clean virtual machines.
2. Acquire a Windows Authenticode certificate and configure Tauri signing.
   Unsigned installers work, but Windows will show an unverified-publisher
   warning. Do not put a certificate or password in the repository.
3. Choose the final HTTPS URL for the Flatpak repository.
4. Upload the extracted contents of the Flatpak repository archive to that URL.
5. Publish a `.flatpakrepo` descriptor containing the final URL and the
   repository's GPG key. Repository signing is intentionally not enabled until
   that key exists; keep the private key only in GitHub Actions secrets.
6. Enable GitHub private vulnerability reporting before making the repository
   public.

Users can test the unsigned bundle artifact directly with:

```bash
flatpak install --user ./Colemak-DH-Tutor-x86_64.flatpak
flatpak run io.github.exolithelabs.ColemakDHTutor
```

The generated prerelease is suitable for testing. Do not promote it to a
public production release until the signing identities and Flatpak hosting URL
are final. Those values cannot be safely guessed in source control.
