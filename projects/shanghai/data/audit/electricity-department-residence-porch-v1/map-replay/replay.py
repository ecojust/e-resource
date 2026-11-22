"""Reproduce the city checks for the electricity department residence porch."""
import gzip
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import urlsplit

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent


def read(file):
    return json.loads(file.read_bytes())


def main():
    pins = read(HERE / 'input-digests.json')
    for name, digest in pins['vendor'].items():
        assert sha256((AUDIT.parents[2] / 'vendor' / name).read_bytes()).hexdigest() == digest, name
    inputs = read(HERE / 'source-318-sightlines.json')
    expected = read(HERE / 'actual-318-camera-city-triangles.json')
    assert sha256((AUDIT / 'final-placement-contract.json').read_bytes()).hexdigest() == inputs['contract_sha256']
    table = HERE / 'actual-318-feature-table.json.gz'
    assert sha256(table.read_bytes()).hexdigest() == inputs['feature_table_sha256']
    routes = {}
    for source in expected['sources']:
        digest = source['sha256']
        body = gzip.decompress((HERE / (digest + '.gz')).read_bytes())
        assert len(body) == source['bytes'] and sha256(body).hexdigest() == digest
        routes[urlsplit(source['url']).path] = body

    class Tiles(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path not in routes:
                self.send_error(404)
                return
            body = routes[self.path]
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    with TemporaryDirectory() as work:
        scratch = Path(work)
        catalog = gzip.decompress((HERE / 'raw-318-catalog.json.gz').read_bytes())
        assert sha256(catalog).hexdigest() == pins['raw_catalog_sha256']
        (scratch / 'catalog.json').write_bytes(catalog)
        subprocess.run([sys.executable, AUDIT / 'make-map-case.py', '--previous-catalog',
                        scratch / 'catalog.json', '--table', table, '--out', scratch / 'case.json'], check=True)
        assert (scratch / 'case.json').read_bytes() == (HERE / 'actual-318-map-case.json').read_bytes()
        with HTTPServer(('127.0.0.1', 0), Tiles) as server:
            thread = Thread(target=server.serve_forever)
            thread.start()
            try:
                subprocess.run(['node', AUDIT / 'trace-registered-city.mjs', HERE / 'source-318-sightlines.json',
                                scratch / 'camera.json', f'http://127.0.0.1:{server.server_port}/'], check=True)
            finally:
                server.shutdown()
                thread.join()
        replay = read(scratch / 'camera.json')
        for after, original in zip(replay['sources'], expected['sources'], strict=True):
            assert urlsplit(after['url']).path == urlsplit(original['url']).path
            after['url'] = original['url']
        assert replay == expected
        print(f"Reproduced {len(replay['results'])} camera rays and the signed ground and neighbor checks.")


if __name__ == '__main__':
    main()
