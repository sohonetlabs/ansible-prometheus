#!/usr/bin/env python3
"""Remove incident roots from the archived CentOS compatibility image."""

import hashlib
import re
import ssl
import subprocess
from pathlib import Path

blocked = {
    "7dd78d5f4f13459a83dff9abbba62edbaf6f2d102bf257fd712f4d9f2746ed8d",
    "f2edaaff3d9b701fb4d14c9f285f8c0bad90fc3bcc1fa07d47f4718edaba34a5",
    "d7a7a0fb5d7e2731d771e9484ebcdef71d5f0c3e0a2948782bc83ee0ea699ef4",
    "86a1ecba089c4a8d3bbe2734c612ba341d813e043cf9e8a862cd5c57a36bbe6b",
}
bundle = Path("/etc/pki/tls/certs/ca-bundle.crt").read_text()
# CentOS 8 uses blacklist; newer p11-kit versions use blocklist.
blocklists = [Path("/etc/pki/ca-trust/source") / name
              for name in ("blacklist", "blocklist")]
for directory in blocklists:
    directory.mkdir(parents=True, exist_ok=True)
for pem in re.findall(
    r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", bundle, re.S
):
    fingerprint = hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest()
    if fingerprint in blocked:
        for directory in blocklists:
            (directory / f"emsign-{fingerprint}.pem").write_text(pem + "\n")
        print(f"Distrusted affected root: {fingerprint}")

subprocess.run(["update-ca-trust", "extract"], check=True)
contexts = [ssl.create_default_context()]
try:
    import certifi
except ImportError:
    pass
else:
    contexts.append(ssl.create_default_context(cafile=certifi.where()))
for context in contexts:
    roots = context.get_ca_certs(binary_form=True)
    if not roots or blocked.intersection(hashlib.sha256(c).hexdigest() for c in roots):
        raise SystemExit("Unsafe or empty CA bundle after distrust update")
print("System and installed certifi CA stores exclude the incident roots")
