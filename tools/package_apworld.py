"""Package worlds/digipelago into a distributable digipelago.apworld zip.

Adds the container manifest keys (compatible_version/version) that Archipelago's
APWorldContainer requires in a zipped apworld; the SOURCE archipelago.json must
not define them (see AP's test_world_manifest), so they are injected here.

Run: python tools/package_apworld.py   ->  dist/digipelago.apworld
"""
from __future__ import annotations

import json
import os
import zipfile

CONTAINER_VERSION = 7  # worlds/Files.py container_version in AP 0.6.7

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "worlds", "digipelago")
OUT_DIR = os.path.join(ROOT, "dist")
OUT = os.path.join(OUT_DIR, "digipelago.apworld")


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(SRC):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                p = os.path.join(root, f)
                arc = "digipelago/" + os.path.relpath(p, SRC).replace(os.sep, "/")
                if arc == "digipelago/archipelago.json":
                    with open(p, encoding="utf-8") as fh:
                        manifest = json.load(fh)
                    manifest["compatible_version"] = CONTAINER_VERSION
                    manifest["version"] = CONTAINER_VERSION
                    z.writestr(arc, json.dumps(manifest, indent=4))
                else:
                    z.write(p, arc)
    with zipfile.ZipFile(OUT) as z:
        manifest = json.loads(z.read("digipelago/archipelago.json"))
    print(f"wrote {OUT} (world_version {manifest.get('world_version')})")


if __name__ == "__main__":
    main()
