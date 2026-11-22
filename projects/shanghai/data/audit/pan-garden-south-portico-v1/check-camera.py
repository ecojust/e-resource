"""Check the public map camera against the cut street corner and retained neighboring buildings."""
from argparse import ArgumentParser
import gzip
import json
import math
from pathlib import Path
import runpy
from shapely.affinity import scale, translate
from shapely.geometry import Point, shape

HERE = Path(__file__).resolve().parent
PROJECT = Path(__file__).resolve().parents[3]
SHARED = runpy.run_path(str(PROJECT/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'))


def eye_points(record):
    return [('左通高石柱',-2.12,-.34,4.14),('右通高石柱',2.12,-.34,6.64),('左柱头',-2.12,-.37,8.47),('中央栏杆帽',0,.12,5.82),('弧阶外缘',0,-2.30,.14),('中央门扇',0,2.76,2.05),('左凸窗裙',-8.04,-.64,4.56),('右凸窗裙',8.04,-.64,4.56),('前檐外挑石线',.22,-.53,9.42),('东端退层窗',7.7,.91,10.49)]


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, default=HERE/'final-placement-contract.json')
    parser.add_argument('--table', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=HERE/'camera-sightlines.json')
    args = parser.parse_args()
    receipt = json.loads(args.contract.read_bytes())
    record = json.loads((Path(__import__('os').environ.get('PAN_SOURCE_ROOT',PROJECT))/'source/precise'/receipt['id']/'footprint-review.json').read_bytes())
    expected = next(b['sha256'] for b in record['frozen_bindings']
                    if b['repository_path'].endswith('/feature-table.json.gz'))
    assert SHARED['digest'](args.table.read_bytes()) == expected
    lon, lat = receipt['lng'], receipt['lat']
    north = math.radians(1)*SHARED['EARTH']
    east = north*math.cos(math.radians(lat))

    def convert(poly):
        return scale(translate(poly, xoff=-lon, yoff=-lat), xfact=east, yfact=north, origin=(0, 0))
    mask = convert(shape(receipt['replacement_geometry']))
    other = []
    for row in json.loads(gzip.decompress(args.table.read_bytes()))['features']:
        geom = shape(row['geometry'])
        if geom.distance(Point(lon, lat)) > .002:
            continue
        geom = convert(geom)
        if geom.distance(Point(0, 0)) > 150:
            continue
        if row['localId'] == 2572:
            geom = geom.difference(mask)
        other.append((row['localId'], geom, row['height']))
    h = math.radians(receipt['heading'])
    targets = [(name, x*math.cos(h)+y*math.sin(h), -x*math.sin(h)+y*math.cos(h), z)
               for name, x, y, z in eye_points(record)]
    choices = [('delivered',receipt['overviewBearing'],receipt['overviewPitch']),
               ('正面',-46,64),('正面高看',-46,30),('偏东斜看',-67,55),('后方原楼体遮挡样本',64,67)]
    cases = {}
    for name, bearing, pitch in choices:
        rows = []
        for label, width, height, padding in SHARED['VIEWS']:
            viewport = dict(width=width, height=height, insets=dict(
                zip(['left', 'right', 'top', 'bottom'], padding)))
            rows.append(SHARED['evaluate']({**receipt, 'overviewBearing': bearing, 'overviewPitch': pitch},
                                           viewport, label, other, lon, lat, east, north, targets))
        cases[name] = rows
    result = {'id': receipt['id'], 'contract_sha256': SHARED['digest'](args.contract.read_bytes()),
              'camera_module_sha256': SHARED['digest']((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
              'retained_volumes': len(other), 'source_sha256': expected, 'cases': cases}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print({key: [v['clear_count'] for v in vset]for key, vset in cases.items()})
    assert all(r['clear_count'] == len(r['probes'])for r in cases['delivered'])


if __name__ == '__main__':
    main()
