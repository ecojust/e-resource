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
PROJECT = HERE.parents[2]
SHARED = runpy.run_path(str(HERE.parent/'pure-heart-church-v1/check-overview-sightlines.py'))


def eye_points(record):
    return [('南坡',-8.9,1.2,7.21124),('北坡',8.88,1.2,7.21113),('中央屋面',-.12,.30,7.05421),
            ('南临院窗',-8.83,0.,5.22),('中央菱格木窗',0.,0.,5.24),('北临院窗',8.83,0.,5.22),
            ('南雕板',-4.31,-.09,3.79),('中央雕板',0.,-.09,3.79),('北雕板',4.31,-.09,3.79),
            ('中轴廊柱',2.64,-.109,2.04),('中央石阶',.40,-.78,.33)]


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, default=HERE/'final-placement-contract.json')
    parser.add_argument('--table', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=HERE/'camera-sightlines.json')
    args = parser.parse_args()
    receipt = json.loads(args.contract.read_bytes())
    record = json.loads((PROJECT/'source/precise'/receipt['id']/'footprint-review.json').read_bytes())
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
    east_table=args.table.with_name('east-feature-table.json.gz')
    assert SHARED['digest'](east_table.read_bytes())=='2d85e7268d04b6d9cdcf43ed6ab906a61b53ef4a489e88f9fa698211c49b43df'
    west=json.loads(gzip.decompress(args.table.read_bytes()))['features']
    east_rows=json.loads(gzip.decompress(east_table.read_bytes()))['features']
    for macro,row in [('west',r)for r in west]+[('east',r)for r in east_rows]:
        geom = shape(row['geometry'])
        if geom.distance(Point(lon, lat)) > .002:
            continue
        geom = convert(geom)
        if geom.distance(Point(0, 0)) > 150:
            continue
        if macro=='west' and row['localId'] == 354:
            geom = geom.difference(mask)
        other.append(((0 if macro=='west' else 10000)+row['localId'], geom, row['height']))
    h = math.radians(receipt['heading'])
    targets = [(name, x*math.cos(h)+y*math.sin(h), -x*math.sin(h)+y*math.cos(h), z)
               for name, x, y, z in eye_points(record)]
    choices=[('delivered',receipt['overviewBearing'],receipt['overviewPitch']),
             ('院中稍偏南',-92,69),('院中稍偏北',-120,61),('低位向西',-108,76),('背墙负控',72,68)]
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
