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
    return [('门棚檐下挂落',0,-1.58,4.18),('门棚上檐',.55,-1.55,3.95),
            ('木门棚左柱',-1.29,-1.438,1.63),('木门棚右柱',1.29,-1.438,1.63),
            ('砖山墙窄阁孔',3.04,.15,7.11),('山尖垂饰',3.04,-.22,8.52),
            ('外挑花栏',3.04,-.24,4.33),('上层白色窗框',3.04,.06,4.9),
            ('右侧檐肩浅石',4.83,-.03,5.50)]


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
        if geom.distance(Point(lon, lat)) > .002:
            continue
        geom = convert(geom)
        if geom.distance(Point(0, 0)) > 150:
            continue
        if row['localId'] == 2157:
            geom = geom.difference(mask)
        other.append((row['localId'], geom, row['height']))
    h = math.radians(receipt['heading'])
    targets = [(name, x*math.cos(h)+y*math.sin(h), -x*math.sin(h)+y*math.cos(h), z)
               for name, x, y, z in eye_points(record)]
    choices = [('delivered',receipt['overviewBearing'],receipt['overviewPitch']),
               ('正面',-116,64),('街侧高看',-116,30),('偏北斜看',-150,55),('后方原楼体遮挡样本',64,67)]
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
