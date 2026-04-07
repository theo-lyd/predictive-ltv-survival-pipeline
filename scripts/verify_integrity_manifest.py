"""Verify integrity manifests for SLA artifacts."""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app.core.sla import get_integrity_manifest_path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(path: Path, signing_key: str | None = None) -> tuple[bool, list[str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []

    for artifact in payload.get("artifacts", []):
        artifact_path = Path(artifact["path"])
        expected = artifact.get("sha256")
        if not artifact_path.exists():
            errors.append(f"Missing artifact: {artifact_path}")
            continue
        actual = _sha256(artifact_path)
        if expected != actual:
            errors.append(f"Checksum mismatch: {artifact_path}")

    signature = payload.get("signature")
    if signature:
        key = signing_key or os.getenv("SLA_INTEGRITY_SIGNING_KEY")
        if not key:
            errors.append("Manifest contains signature but no signing key provided")
        else:
            unsigned_payload = {k: v for k, v in payload.items() if k != "signature"}
            message = json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
            expected_sig = hmac.new(key.encode("utf-8"), message, hashlib.sha256).hexdigest()
            if expected_sig != signature.get("value"):
                errors.append("Signature verification failed")

    return len(errors) == 0, errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify SLA artifact integrity manifest")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=get_integrity_manifest_path(),
        help="Path to integrity manifest JSON",
    )
    parser.add_argument(
        "--signing-key",
        help="Optional signing key override for HMAC signature verification",
    )
    args = parser.parse_args(argv)

    ok, errors = verify_manifest(args.manifest, args.signing_key)
    if ok:
        print("Integrity manifest verification PASSED")
        return 0

    print("Integrity manifest verification FAILED")
    for item in errors:
        print(f"- {item}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
