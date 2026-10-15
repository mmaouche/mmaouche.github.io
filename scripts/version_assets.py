#!/usr/bin/env python3
"""Update local CSS/JavaScript URLs so browsers fetch the matching release."""
import argparse
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ASSET_URL = re.compile(r'''(?P<start>\b(?:src|href)=["'])(?P<path>assets/[^"'?]+\.(?:css|js))(?:\?v=[a-f0-9]+)?(?P<end>["'])''')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check without editing index.html')
    args = parser.parse_args()
    page = ROOT / 'index.html'
    original = page.read_text(encoding='utf-8')

    def version(match):
        asset = (ROOT / match['path']).resolve()
        if ROOT not in asset.parents:
            raise ValueError('Asset is outside the website directory')
        digest = hashlib.sha256(asset.read_bytes()).hexdigest()[:12]
        return f'{match["start"]}{match["path"]}?v={digest}{match["end"]}'

    updated = ASSET_URL.sub(version, original)
    if args.check:
        if updated != original:
            parser.exit(1, 'Asset versions need updating: run python3 scripts/version_assets.py\n')
        print('Asset versions match the current CSS and JavaScript.')
    elif updated != original:
        page.write_text(updated, encoding='utf-8')
        print('Updated CSS and JavaScript versions in index.html.')
    else:
        print('Asset versions are already current.')


if __name__ == '__main__':
    main()
