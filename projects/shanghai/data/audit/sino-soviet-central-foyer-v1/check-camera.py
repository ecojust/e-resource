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
    return [('中央门楣外檐',0.,-.745,20.55),('拱券外石面',-.15,-.195,16.91),
            ('东门柱的方形柱头',9.42,-.911,16.44),('西门柱的方形柱头',-9.42,-.911,16.44),
            ('东亭窗顶的石檐',19.40,.34,27.34),('西亭窗顶的石檐',-19.40,.34,27.34),
            ('东亭金顶',19.40,1.81,29.14),('西亭金顶',-19.40,1.81,29.14),
            ('前排西端列柱',-10.335,11.52,36.01),('前排东端列柱',10.335,11.52,36.01),
            ('西侧塔层',-7.33,11.30,41.91),('上层方檐',0.,17.31,61.445),
            ('鎏金长塔身',0.,22.42,89.56),('红色五星',0.,22.795,112.04)]


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
    for row in json.loads(gzip.decompress(args.table.read_bytes()))['features']:
        geom = shape(row['geometry'])
        if geom.distance(Point(lon, lat)) > .004:
            continue
        geom = convert(geom)
        if geom.distance(Point(0, 0)) > 285:
            continue
        if row['localId'] == 969:
            geom = geom.difference(mask)
        other.append((row['localId'], geom, row['height']))
    h = math.radians(receipt['heading'])
    targets = [(name, x*math.cos(h)+y*math.sin(h), -x*math.sin(h)+y*math.cos(h), z)
               for name, x, y, z in eye_points(record)]
    choices = [('delivered',receipt['overviewBearing'],receipt['overviewPitch']),
               ('广场直视',-23,67),('南广场东侧',-40,57),('南广场西侧',-6,57),('北面负控',155,54)]
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
