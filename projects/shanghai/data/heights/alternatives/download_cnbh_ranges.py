"""Explicitly download the public CNBH-10m source tile; never runs on import.

The 335 MB raw source must not be committed to Git. A valid existing file and
completed byte-range chunks are reused. Downloaded content is MD5-verified.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
SOURCE_URL = 'https://zenodo.org/api/records/7827315/files/CNBH10m_X121Y31.tif/content'
SOURCE_BYTES = 335234763
SOURCE_MD5 = '72fccc03160010daeb697220e2c0db1b'


def file_md5(path):
    digest = hashlib.md5()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 2**20), b''):
            digest.update(block)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE.parent/'.cache'/'height-sources'/'CNBH10m_X121Y31.tif',
                        help='Raw source destination; default: data/heights/.cache/height-sources/CNBH10m_X121Y31.tif')
    parser.add_argument('--workers', type=int, default=6, help='Concurrent public HTTP range requests (default: 6)')
    parser.add_argument('--chunk-mib', type=int, default=8, help='Resumable chunk size in MiB (default: 8)')
    args = parser.parse_args(argv)
    if args.workers < 1 or args.chunk_mib < 1:
        parser.error('--workers and --chunk-mib must be positive')
    output = args.output.resolve()
    if output.exists() and output.stat().st_size == SOURCE_BYTES and file_md5(output) == SOURCE_MD5:
        print(json.dumps({'path': str(output), 'bytes': SOURCE_BYTES, 'md5': SOURCE_MD5, 'cached': True}))
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    parts = output.with_name(output.name + '.parts')
    parts.mkdir(exist_ok=True)
    chunk_size = args.chunk_mib * 2**20
    started = time.monotonic()

    def fetch(index):
        low = index * chunk_size
        high = min(SOURCE_BYTES-1, low + chunk_size-1)
        part = parts / f'{low:012}-{high:012}.bin'
        if part.exists() and part.stat().st_size == high-low+1:
            return index, part, True
        for attempt in range(4):
            try:
                request = Request(SOURCE_URL, headers={'Range': f'bytes={low}-{high}'})
                with urlopen(request, timeout=90) as response:
                    if response.status != 206 or response.headers.get('Content-Range') != f'bytes {low}-{high}/{SOURCE_BYTES}':
                        raise IOError('Source did not honor the requested public byte range')
                    data = response.read()
                if len(data) != high-low+1:
                    raise IOError('Truncated download chunk')
                temporary = part.with_suffix('.tmp')
                temporary.write_bytes(data)
                temporary.replace(part)
                return index, part, False
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2**attempt)

    count = math.ceil(SOURCE_BYTES/chunk_size)
    downloaded = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(fetch, index) for index in range(count)]):
            index, path, cached = future.result()
            downloaded[index] = path
            print(f'chunk {index+1}/{count}: {"cached" if cached else "downloaded"}', flush=True)
    temporary = output.with_name(output.name + '.tmp')
    digest = hashlib.md5()
    with temporary.open('wb') as stream:
        for index in range(count):
            data = downloaded[index].read_bytes()
            stream.write(data)
            digest.update(data)
    if digest.hexdigest() != SOURCE_MD5:
        raise IOError(f'Official MD5 mismatch: {digest.hexdigest()}')
    temporary.replace(output)
    print(json.dumps({'path': str(output), 'bytes': output.stat().st_size, 'md5': SOURCE_MD5,
                      'license': 'CC-BY-4.0', 'seconds': round(time.monotonic()-started, 2)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
