# Releasing

## What CI produces

The **Desktop build** workflow runs on pull requests, pushes to `master`, version
tags, and manual dispatches. It produces:

- an unsigned Windows NSIS `.exe` installer;
- a Linux `.flatpak` bundle for direct testing; and
- `Colemak-DH-Tutor-flatpak-repo.tar.gz`, an OSTree repository ready to upload
  to your static Flatpak host.

Ordinary builds retain these as workflow artifacts for 14 days. Pushing a
version tag creates or updates a draft GitHub Release and attaches the packaged
applications. This uses the automatic per-run `GITHUB_TOKEN`; no personal access
token or custom secret is required.

## Creating a release candidate

Ensure the version matches in `package.json`, `src-tauri/Cargo.toml`,
`src-tauri/tauri.conf.json`, and the Flatpak metainfo, then push the commit and a
matching version tag:

```bash
git tag v0.1.0
git push origin master v0.1.0
```

Wait for both platform jobs to pass, install-test their outputs, and publish the
draft Release from GitHub when it is ready.

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

The generated draft is suitable for internal testing. Do not publish it as a
public production release until the signing identities and Flatpak hosting URL
are final. Those values cannot be safely guessed in source control.
