"""Verify the two real map origins and expose their signed inputs to Node for one phase."""
from contextlib import contextmanager
from pathlib import Path
from urllib.request import urlopen
import fcntl
import hashlib
import json
import os
import tempfile

HOST = Path('/tmp/shanghai-main-262/formal-31262')
ASSET = 'huangpu-nanshi-telephone-exchange'
CANDIDATES = 'data/candidate-city-integrations.json'
MODULES = ('src/app.js', 'src/map-scene.js', 'src/candidate-overview-camera.js',
           'src/candidate-city-clipping.js', 'src/candidate-city-integrations.js',
           'src/building-beacons.js', 'src/building-beacon-groups.js',
           'index.html', 'landmarks.html', CANDIDATES, 'data/precise-buildings-v6.json')


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def writable_area():
    roots = (Path('/run/codex-docker/user'), Path('/dev/shm'), Path('/tmp'))
    def available(path):
        stat = os.statvfs(path)
        return stat.f_bavail * stat.f_frsize
    errors = []
    for base in sorted(roots, key=available, reverse=True):
        try:
            area = base / 'nanshi-262-runtime'
            area.mkdir(exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=area) as handle:
                handle.write(b'physical write')
                handle.flush()
            return area
        except OSError as exc:
            errors.append(str(exc))
    raise OSError('; '.join(errors))


@contextmanager
def live_inputs():
    descriptors = {}
    rows = []
    checks = json.loads((HOST/'signed-comparison.json').read_bytes())['stages']
    with tempfile.TemporaryDirectory(prefix='real-origins-', dir=writable_area()) as temp:
        root = Path(temp)
        try:
            for stage in checks:
                order = stage['n']
                assert order in (261, 262)
                book = HOST / f'{order}-production.json'
                assert digest(book) == stage['production_sha256']
                hashes = json.loads(book.read_bytes())['files']
                names = list(MODULES)
                if order == 262:
                    names.append(f'assets/models/candidates/{ASSET}/manifest.json')
                for name in names:
                    required = hashes[name]
                    # Actually request both origins even when a module is identical.
                    sha = hashlib.sha256()
                    new = required not in descriptors
                    if new:
                        descriptors[required] = os.memfd_create('nanshi-'+Path(name).name, os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
                    with urlopen(stage['origin']+name, timeout=90) as reply:
                        assert reply.status == 200 and reply.url == stage['origin']+name
                        size = 0
                        while chunk := reply.read(131072):
                            sha.update(chunk)
                            size += len(chunk)
                            if new:
                                view = memoryview(chunk)
                                while view:
                                    view = view[os.write(descriptors[required], view):]
                    assert sha.hexdigest() == required, (order, name)
                    fd = descriptors[required]
                    if new:
                        fcntl.fcntl(fd, getattr(fcntl, 'F_ADD_SEALS', 1033), 15)
                    assert fcntl.fcntl(fd, getattr(fcntl, 'F_GET_SEALS', 1034)) & 15 == 15
                    target = root / str(order) / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.symlink_to(f'/proc/{os.getpid()}/fd/{fd}')
                    assert digest(target) == required and target.stat().st_size == size
                    rows.append(dict(stage=order, file=name, bytes=size, sha256=required))
            name = f'source/precise/{ASSET}/footprint-review.json'
            target = root/'262'/name
            source = HOST/'stage262'/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(source)
            assert digest(target) == digest(source)
            yield root, rows
        finally:
            for fd in descriptors.values():
                os.close(fd)
