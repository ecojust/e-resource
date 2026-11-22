"""First surfaces of the complete, unfiltered GLB, including shafts and daylight gaps."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'source'), str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from courtyard_photo_plane import CAMERA, P
import garden_terrace as terrace

# Measured by inspection of the native 2144×1424 picture. Several darker gaps
# contain household plants or fabric. Only separately legible masonry is selected.
PHOTO = {'pier':[(929,402),(940,394),(952,384),(959,370),(1069,349),(1080,336),(1095,344),(1107,369)],
         'spindle':[(980,375),(1005,374),(1018,368),(1129,391),(1141,388),(1166,402),
                    (1190,405),(1201,405),(1277,449),(1302,465)],
         'handrail':[(999,354),(1017,348),(1031,338),(1130,351),(1154,362),(1177,378),(1205,392),(1234,407),(1270,430)],
         'upper moulding':[(901,455),(939,438),(987,419),(1032,401),(1074,386),(1109,402),(1166,429),(1221,455)],
         'deep fascia':[(906,474),(949,457),(997,439),(1039,422),(1075,408),(1120,430),(1174,456),(1228,482),(1282,482)],
         'lower belt':[(972,511),(1011,496),(1050,481),(1076,473),(1107,482),(1138,488),(1174,507)]}


def inspect(path):
    scene = SerialScene(path)
    data = json.loads(terrace.MEASUREMENTS.read_text())
    origin = CAMERA['camera_origin_xyz_m']
    physical, optical = [], []
    def test(tag, start, direction, distance, accepted=None, min_clear=None, photo=None):
        hit = scene.ray(start, direction, distance)
        material = hit['material'] if hit else None
        depth = round(hit['distance_m'],5) if hit else None
        good = (not hit or depth>min_clear) if min_clear is not None else material in accepted
        row={'target':tag,'first_material':material,'distance_m':depth,'passed':bool(good)}
        if photo:
            row['native_pixel']=list(photo);optical.append(row)
        else:
            row['start_xyz_m']=list(start);row['unit_direction']=direction;physical.append(row)
    for face, run in data['runs'].items():
        side = face=='side'
        d = [0,1,0] if side else [-1,0,0]
        def start(s,z):
            return [s,-.31,z] if side else [2.27,s,z]
        centers = run['center_positions']
        for i,s in enumerate(centers,1):
            for z in [7.56,7.70,7.825,7.89,7.945]:
                test(f'{face} spindle {i} at {z}',start(s,z),d,.69,[terrace.STONE])
        for i,(a,b) in enumerate(zip(centers,centers[1:]),1):
            for z in [7.63,7.74,7.88]:
                test(f'{face} gap {i} at {z}',start((a+b)/2,z),d,.83,min_clear=.57)
        for s in centers:
            test(f'{face} top rail',start(s,8.052),d,.68,[terrace.CAP])
    for pier in data['piers']:
        x0,x1,y0,y1,z0,z1=pier['box']
        for face,n in [('side',pier['side_reeds']),('front',pier['front_reeds'])]:
            for i in range(n):
                for z in [7.60,7.79,8.034]:
                    o=[x0+(x1-x0)*(i+.5)/n,-.32,z] if face=='side' else [2.3,y0+(y1-y0)*(i+.5)/n,z]
                    test(f"{pier['key']} {face} reed {i+1}",o,[0,1,0] if face=='side' else [-1,0,0],.59,[terrace.STONE])
    for s in [.27,.72,1.22,1.70]:
        for z,material in [(7.352,terrace.CAP),(7.137,terrace.FASCIA),(6.953,terrace.UNDER),(6.696,terrace.FASCIA)]:
            test('short return', [s,-.4,z],[0,1,0],.70,[material])
    for s in [.34,.94,1.62,2.34,3.17,3.73]:
        for z,material in [(7.352,terrace.CAP),(7.137,terrace.FASCIA),(6.953,terrace.UNDER),(6.696,terrace.FASCIA)]:
            test('front return',[2.35,s,z],[-1,0,0],.72,[material])
    choices={'pier':[terrace.STONE],'spindle':[terrace.STONE],'handrail':[terrace.CAP,terrace.STONE],
             'upper moulding':[terrace.CAP],'deep fascia':[terrace.FASCIA],'lower belt':[terrace.FASCIA]}
    for name, points in PHOTO.items():
        for px in points:
            test(name,origin,np.linalg.solve(P[:,:3],[*px,1.]),45,choices[name],photo=px)
    return dict(asset=scene.asset,method='First triangle of any material, decoded mesh. Physical gap probes must go beyond the entire front railing depth. Original photograph pixels are independent manual surface labels.',
                physical_count=len(physical),physical_matched=sum(r['passed'] for r in physical),
                original_pixels=len(optical),photo_matched=sum(r['passed'] for r in optical),physical=physical,photographic=optical)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('decoded_glb',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();j=inspect(args.decoded_glb);args.output.write_text(json.dumps(j,indent=2)+'\n')
    print(j['physical_matched'], '/',j['physical_count'], 'physical;',j['photo_matched'],'/',j['original_pixels'],'photo')
    for r in j['physical']+j['photographic']:
        if not r['passed']: print(r['target'],r.get('native_pixel',r.get('start_xyz_m')),r['first_material'])
    raise SystemExit(int(j['physical_matched']!=j['physical_count']))
