#!/usr/bin/env python3
"""Redact local personal details from an OpenCode session export.

The full transcript is part of the submission, but it should not publish the
student's local username, home directory or email address. This script walks
every string in the export and applies the replacements below.

Usage:
    python tools/sanitize_chat.py docs/chat_export.json
"""

import json
import sys
from pathlib import Path

REPLACEMENTS = {
    "nonconformistrizwan@gmail.com": "<redacted-email>",
    "TheNonConformist": "<redacted-github-user>",
    "/home/nonconformist/": "/home/student/",
    "nonconformist": "student",
}


def clean(value):
    if isinstance(value, str):
        for old, new in REPLACEMENTS.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    return value


def main(path):
    destination = Path(path)
    data = json.loads(destination.read_text())
    destination.write_text(json.dumps(clean(data), indent=2, ensure_ascii=False) + "\n")
    print(f"sanitized {destination} ({destination.stat().st_size} bytes)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python tools/sanitize_chat.py SESSION.json", file=sys.stderr)
        raise SystemExit(2)
    main(sys.argv[1])
