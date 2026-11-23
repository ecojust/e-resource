"""Check the public map camera against the cut street corner and retained neighboring buildings."""
from argparse import ArgumentParser
import gzip
import json
import math
from os import environ
from pathlib import Path
import runpy
from shapely.affinity import scale, translate
from shapely.geometry import Point, shape

HERE = Path(__file__).resolve().parent
PROJECT = Path(__file__).resolve().parents[3]
PROJECT = Path(environ.get('SHANGHAI_PROJECT', PROJECT))
SHARED = runpy.run_path(str(PROJECT/'data/audit/pure-heart-church-v1/check-overview-sightlines.py'))


def eye_points(record):
    return [('东门廊横檐',.83,-.188,4.41),('横檐滴水线',-.60,-.202,4.52),('左上百叶',-.32,.034,6.65),('右上百叶',.46,.035,6.06),('上层窗台',.30,-.138,5.713),('正面灰墙',.98,-.003,6.70),('西返面圆窗',1.218,1.14,6.52),('西返面灰墙',1.407,.50,7.36)]


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--contract', type=Path, default=HERE/'final-placement-contract.json')
    parser.add_argument('--table', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=HERE/'camera-sightlines.json')
    parser.add_argument('--choose-from-decoded', type=Path, help='Measure candidate angles against the real decoded near and far meshes.')
    args = parser.parse_args()
    receipt = json.loads(args.contract.read_bytes())
    record = json.loads((Path(__import__('os').environ.get('FUXING_GARDEN_SOURCE_ROOT',PROJECT))/'source/precise'/receipt['id']/'footprint-review.json').read_bytes())
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
        if row['localId'] == 484:
            geom = geom.difference(mask)
        other.append((row['localId'], geom, row['height']))
    h = math.radians(receipt['heading'])
    targets = [(name, x*math.cos(h)+y*math.sin(h), -x*math.sin(h)+y*math.cos(h), z)
               for name, x, y, z in eye_points(record)]
    choices = [('delivered',receipt['overviewBearing'],receipt['overviewPitch']),
               ('正面',171.04,61),('正面高看',132,34),('偏东斜看',127,62),('从原宅背面看的遮挡样本',-9,67)]
    def evaluate(bearing,pitch):
        rows=[]
        for label,width,height,padding in SHARED['VIEWS']:
            viewport=dict(width=width,height=height,insets=dict(zip(['left','right','top','bottom'],padding)))
            rows.append(SHARED['evaluate']({**receipt,'overviewBearing':bearing,'overviewPitch':pitch},viewport,label,other,lon,lat,east,north,targets))
        return rows

    if args.choose_from_decoded:
        import numpy as np
        helper=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
        meshes={level:helper['SerialScene'](args.choose_from_decoded/f'decoded-{level}.glb') for level in ('full','lod')}
        local_targets=eye_points(record);attempts=[];chosen=None
        angles=[(132,47),(127,49),(122,46),(136,43),(122,41),(118,37),(112,39),(127,33),(119,31),(132,57),(119,58),(126,62)]
        for bearing,pitch in angles:
            screens=evaluate(bearing,pitch);hits=[]
            for view in screens:
                e,n,z=view['camera_enu'];eye=np.array([e*math.cos(h)-n*math.sin(h),e*math.sin(h)+n*math.cos(h),z])
                for level,model in meshes.items():
                    for label,x,y,z in local_targets:
                        direction=np.array([x,y,z])-eye;dist=np.linalg.norm(direction)
                        hit=model.ray(eye,direction,float(dist)+.07)
                        delta=float(dist-hit['distance_m']) if hit else None
                        hits.append({'view':view['view'],'level':level,'target':label,'first':hit,'delta_m':delta,'clear':delta is not None and abs(delta)<.13})
            good=all(x['clear_count']==len(local_targets) for x in screens) and all(q['clear']for q in hits)
            attempts.append(dict(bearing=bearing,pitch=pitch,screen_counts=[q['clear_count']for q in screens],self_hits=hits,passed=good))
            if good:
                chosen=[bearing,pitch];break
        report={'id':receipt['id'],'preselection_contract_sha256':SHARED['digest'](args.contract.read_bytes()),'model_geometry_sha256':receipt['model_geometry_sha256'],'trials':attempts,'selected':chosen}
        args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        if not chosen:raise ValueError('No tested camera showed the eight selected surfaces on both devices and both LODs.')
        print('selected',chosen,len(attempts));return
    cases={name:evaluate(bearing,pitch)for name,bearing,pitch in choices}
    result = {'id': receipt['id'], 'contract_sha256': SHARED['digest'](args.contract.read_bytes()),
              'camera_module_sha256': SHARED['digest']((PROJECT/'src/candidate-overview-camera.js').read_bytes()),
              'retained_volumes': len(other), 'source_sha256': expected, 'cases': cases}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print({key: [v['clear_count'] for v in vset]for key, vset in cases.items()})
    assert all(r['clear_count'] == len(r['probes'])for r in cases['delivered'])


if __name__ == '__main__':
    main()
