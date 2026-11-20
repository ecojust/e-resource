"""Fetch the four immutable V4.4 public assets to a separate build directory."""
from hashlib import sha1,sha256
import json
from pathlib import Path
import sys
import tempfile
from urllib.request import urlopen


def matches(data, record):
    git=sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    return git==record['git_blob'] and len(data)==record['bytes'] and sha256(data).hexdigest()==record['sha256']


def main():
    baseline=json.loads(Path(__file__).with_name('baseline.json').read_bytes())
    directory=Path(sys.argv[1]);directory.mkdir(exist_ok=True,parents=True)
    for record in baseline['assets'].values():
        target=directory/record['file']
        if target.exists():
            if not matches(target.read_bytes(),record):
                raise ValueError(f'Existing file differs from the V4.4 baseline: {target}')
            continue
        url=f"https://raw.githubusercontent.com/{baseline['project']}/{baseline['commit']}/projects/shanghai/{record['path']}"
        with urlopen(url,timeout=120)as response:
            data=response.read()
        if not matches(data,record):
            raise ValueError(f'Incomplete or different V4.4 asset at {url}')
        with tempfile.NamedTemporaryFile(dir=directory,delete=False)as temporary:
            temporary.write(data)
            saved=Path(temporary.name)
        saved.replace(target)
        print(target,record['sha256'])


if __name__=='__main__':
    main()
