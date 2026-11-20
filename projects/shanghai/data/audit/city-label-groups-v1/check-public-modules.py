"""Verify the published module URLs loaded by the city map's building labels."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parents[5]
PREFIX = 'projects/shanghai/'
PUBLIC = 'https://raw.githack.com/ecojust/e-resource/'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('commit')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    commit = subprocess.check_output(
        ['git', 'rev-parse', '--verify', args.commit + '^{commit}'], cwd=REPO, text=True
    ).strip()
    records = []

    def verify(relative):
        path = urlsplit(relative).path
        local = subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=REPO)
        url = PUBLIC + commit + '/' + relative
        with urlopen(Request(url, headers={'User-Agent': 'Shanghai model publication verification'}), timeout=40) as response:
            data = response.read()
            assert response.status == 200 and data == local, url
        records.append(dict(url=url, path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        return data.decode('utf-8')

    page = PREFIX + 'index.html'
    entry, = re.findall(r'<script type="module" src="([^"]+)"', verify(page))
    module = urljoin(page, entry)
    for dependency in ('map-scene', 'building-beacons', 'building-beacon-groups'):
        expression = r"""from\s*['"](\./""" + re.escape(dependency) + r"""\.js\?[^'"]+)['"]"""
        relative, = re.findall(expression, verify(module))
        module = urljoin(module, relative)
    verify(module)
    args.output.write_text(json.dumps(dict(passed=True, commit=commit,
        checked_at_utc=datetime.now(timezone.utc).isoformat(), files=records), indent=2) + '\n')


if __name__ == '__main__':
    main()
