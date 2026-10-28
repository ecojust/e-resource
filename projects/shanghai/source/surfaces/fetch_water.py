"""Freeze the water layer at z14 for every tile intersecting the 16 districts.

Raw source hashes identify the downloaded responses; frozen PBFs contain ONLY
that response's water layer (protobuf copy, not a geometry re-encoding).
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
import zipfile
from urllib.request import Request, urlopen

from mapbox_vector_tile.Mapbox import vector_tile_pb2
from shapely.geometry import box, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
ZOOM = 14


def fetch(url):
    for attempt in range(4):
        try:
            with urlopen(Request(url, headers={'User-Agent': 'ShanghaiSurfaceStudy/1.0 (OpenStreetMap attribution retained)'}), timeout=30) as response:
                return response.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(1 + attempt)


def latitude(y):
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / 2**ZOOM))))


def bounds(x, y):
    n = 2**ZOOM
    return [x / n * 360 - 180, latitude(y + 1), (x + 1) / n * 360 - 180, latitude(y)]


def required_tiles(districts):
    area = unary_union([shape(f['geometry']) for f in districts['features']])
    west, south, east, north = area.bounds
    xt = lambda lng: math.floor((lng + 180) / 360 * 2**ZOOM)
    yt = lambda lat: math.floor((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2**ZOOM)
    return [(x, y) for x in range(xt(west), xt(east) + 1)
            for y in range(yt(north), yt(south) + 1) if area.intersects(box(*bounds(x, y)))]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    snapshot = ROOT / 'snapshot'
    snapshot.mkdir(exist_ok=True)
    boundary = (PROJECT / 'data/districts.geojson').read_bytes()
    tiles = required_tiles(json.loads(boundary))
    tilejson_path = ROOT / 'tilejson.json'
    if not tilejson_path.exists():
        tilejson_path.write_bytes(fetch('https://tiles.openfreemap.org/planet'))
    tilejson = json.loads(tilejson_path.read_bytes())
    template = tilejson['tiles'][0]
    if '{z}' not in template or template == 'https://tiles.openfreemap.org/planet/{z}/{x}/{y}.pbf':
        raise ValueError('Need a dated, immutable tile URL')

    def download(tile):
        x, y = tile
        name = f'{ZOOM}-{x}-{y}'
        meta_path = snapshot / f'{name}.json'
        path = snapshot / f'{name}.water.pbf'
        if meta_path.exists() and path.exists():
            record = json.loads(meta_path.read_bytes())
            if record['sha256'] == sha(path.read_bytes()) and record['url'] == template.format(z=ZOOM, x=x, y=y):
                return record
        url = template.format(z=ZOOM, x=x, y=y)
        raw = fetch(url)
        source = vector_tile_pb2.tile()
        source.ParseFromString(raw)
        water = vector_tile_pb2.tile()
        count = 0
        for layer in source.layers:
            if layer.name == 'water':
                water.layers.add().CopyFrom(layer)
                count += len(layer.features)
        data = water.SerializeToString()
        path.write_bytes(data)
        record = {'tile': [ZOOM, x, y], 'bounds': bounds(x, y), 'url': url,
                  'raw_bytes': len(raw), 'raw_sha256': sha(raw), 'file': path.name,
                  'bytes': len(data), 'sha256': sha(data), 'water_features': count,
                  'retrieved_utc': datetime.now(timezone.utc).isoformat()}
        meta_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        return record

    records = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 12))) as pool:
        pending = {pool.submit(download, tile): tile for tile in tiles}
        for future in as_completed(pending):
            records.append(future.result())
            if len(records) % 100 == 0 or len(records) == len(tiles):
                print(f'{len(records)}/{len(tiles)} tiles frozen', flush=True)
    records.sort(key=lambda r: r['tile'])
    manifest = {'version': 1, 'zoom': ZOOM, 'boundary_sha256': sha(boundary),
                'attribution': '© OpenStreetMap contributors; OpenFreeMap / OpenMapTiles',
                'license': 'ODbL-1.0', 'source_template': template,
                'snapshot_kind': 'Copied water protobuf layer only; raw response hashes retained, other layers omitted.',
                'tiles': records}
    with zipfile.ZipFile(ROOT / 'water-tiles.zip', 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for record in records:
            info = zipfile.ZipInfo(record['file'], date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (snapshot / record['file']).read_bytes())
    (ROOT / 'sources.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'tiles': len(records), 'water_features_before_union': sum(r['water_features'] for r in records),
                      'frozen_bytes': sum(r['bytes'] for r in records)}, indent=2), flush=True)


if __name__ == '__main__':
    main()
