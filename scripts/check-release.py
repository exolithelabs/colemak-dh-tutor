"""Validate release identity before expensive packaging or publication."""
import json
import os
from pathlib import Path
import re
import tomllib
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
version = json.loads((root / "package.json").read_text())["version"]
versions = [
    json.loads((root / "package-lock.json").read_text())["version"],
    json.loads((root / "src-tauri/tauri.conf.json").read_text())["version"],
    tomllib.loads((root / "src-tauri/Cargo.toml").read_text())["package"]["version"],
    next(package["version"] for package in tomllib.loads((root / "src-tauri/Cargo.lock").read_text())["package"]
         if package["name"] == "colemak-dh-tutor"),
    ET.parse(root / "packaging/flatpak/io.github.exolithelabs.ColemakDHTutor.metainfo.xml")
    .find("./releases/release").attrib["version"],
]
if any(value != version for value in versions):
    raise SystemExit(f"Application versions disagree: {version}, {versions}")
if os.environ.get("GITHUB_REF_TYPE") == "tag":
    tag = os.environ["GITHUB_REF_NAME"]
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag) or tag != f"v{version}":
        raise SystemExit(f"Release tag must match application version v{version}")
print(f"Application version verified: {version}")
