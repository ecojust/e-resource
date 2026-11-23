"""Check the ten reconstructed metal letters and the counters of A and O in the actual GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import polylabel

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene


def run(glb,local):
    letters=json.loads((HERE/'eight-chimney-lettering.json').read_bytes())
    cams=json.loads((HERE/'six-front-cameras.json').read_bytes())['houses']['8']['views']
    if not local:
        station=json.loads((HERE/'courtyard-front-station.json').read_bytes())
        cams={**cams,'winter2023-04 courtyard':{'world_to_upright_pixel_camera':station['house8_to_upright_pixel_camera']}}
    frame=json.loads((HERE.parent/'source/garden-layout.json').read_bytes())['8']['garden_transform']
    to_world=np.eye(4)
    if not local:
        to_world[:2,0]=frame['local_X_unit_EN'];to_world[:2,1]=frame['local_Y_unit_EN']
        to_world[:2,3]=frame['left_wall_projection']['garden_ENU_m']
    scene=SerialScene(glb);probes=[]
    for item in letters['letters']:
        outline=Polygon(item['outer_xz'],item['inner_xz']);spots=[('metal',polylabel(outline,tolerance=.002))]
        spots.extend(('counter',polylabel(Polygon(h),tolerance=.002)) for h in item['inner_xz'])
        for surface,spot in spots:
            sample=[spot.x,letters['face_y_m'],spot.y,1]
            for tag,c in cams.items():
                p=np.array(c['world_to_upright_pixel_camera']);uv=p@sample;uv=uv[:2]/uv[2]
                world_p=p@np.linalg.inv(to_world);inv=np.linalg.inv(world_p[:,:3]);eye=-inv@world_p[:,3]
                hit=scene.ray(eye,inv@np.r_[uv,1.],120)
                metal=bool(hit and hit['material']=='Hongji 8 | rust coloured metal lettering')
                probes.append({'rank':item['rank'],'letter':item['letter'],'surface':surface,'view':tag,
                               'native_uv':uv.round(2).tolist(),'local_xz':[spot.x,spot.y],
                               'first_hit':hit,'matched':bool(hit and metal==(surface=='metal'))})
    return {'glb_sha256':hashlib.file_digest(glb.open('rb'),'sha256').hexdigest(),'asset_frame':'local'if local else'garden ENU',
            'method':'Each probe uses an interior point of the original 2016 sourced outline or counter, registered into all three original front views. Other epochs and foreground foliage can obscure individual letters.',
            'samples':probes,'rays':len(probes),'matches':sum(s['matched']for s in probes)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--local',action='store_true',help='Use a house 8 local-frame mesh')
    r=parser.parse_args();results=run(r.glb,r.local)
    r.output.write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print(results['matches'],results['rays'])
