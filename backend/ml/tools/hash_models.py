"""Generate / refresh ``backend/ml/models/CHECKSUMS.json``.

Run this *after* retraining a model so the registry will accept the
new artifact. The manifest is just a JSON dict of ``{filename: sha256}``.

Usage::

    python -m ml.tools.hash_models

Optionally pass ``--check`` to verify the current files against the
manifest and exit non-zero on mismatch. This is what CI should run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
MANIFEST = MODELS_DIR / "CHECKSUMS.json"

# Extensions we hash. Joblib produces .joblib; we also include the
# auxiliary .json so a swap of any companion file is caught.
HASHED_SUFFIXES = (".joblib", ".json", ".pkl", ".bin")


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def compute() -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(MODELS_DIR.iterdir()):
        if not p.is_file() or p.suffix not in HASHED_SUFFIXES:
            continue
        if p.name == MANIFEST.name:
            continue
        out[p.name] = _sha256_of_file(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--check",
        action="store_true",
        help="Verify existing files against the manifest. Exits non-zero on mismatch.",
    )
    args = ap.parse_args()

    if not MODELS_DIR.exists():
        print(f"Models directory not found: {MODELS_DIR}", file=sys.stderr)
        return 1

    if args.check:
        if not MANIFEST.exists():
            print("CHECKSUMS.json is missing — run without --check first.", file=sys.stderr)
            return 1
        with open(MANIFEST, "r", encoding="utf-8") as f:
            expected = json.load(f)
        rc = 0
        actual = compute()
        for name, want in expected.items():
            got = actual.get(name)
            if got is None:
                print(f"MISSING: {name}", file=sys.stderr)
                rc = 1
                continue
            if got != want:
                print(f"MISMATCH: {name} expected {want[:12]}... got {got[:12]}...", file=sys.stderr)
                rc = 1
        for name in actual:
            if name not in expected:
                print(f"UNEXPECTED: {name} not in manifest", file=sys.stderr)
                rc = 1
        if rc == 0:
            print(f"OK — {len(expected)} model files verified.")
        return rc

    new = compute()
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(new, f, indent=2, sort_keys=True)
        f.write("\n")
    print(f"Wrote {MANIFEST} with {len(new)} entries.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
