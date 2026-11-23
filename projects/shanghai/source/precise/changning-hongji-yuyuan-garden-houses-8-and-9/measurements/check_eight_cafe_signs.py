"""Check the three signs from their recorded photo pixels against an unfiltered GLB."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import numpy as np

D = Path(__file__).resolve().parent
sys.path.insert(0,str(D.parents[3]/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene


def verify(asset, output, local=False):
    data = json.loads((D/'eight-cafe-sign-observations.json').read_bytes())
    registry = json.loads((D/'house-eight-entrance-observations.json').read_bytes())['views']
    cameras = {key:value['P'] for key,value in registry.items()}
    cameras['winter2023-04-courtyard'] = json.loads((D/'courtyard-front-station.json').read_bytes())['house8_to_upright_pixel_camera']
    transform = np.eye(4)
    if not local:
        frame = json.loads((D.parent/'source/garden-layout.json').read_bytes())['8']['garden_transform']
        transform[:2,:2] = np.transpose([frame['local_X_unit_EN'],frame['local_Y_unit_EN']])
        transform[:2,3] = frame['left_wall_projection']['garden_ENU_m']
    scene = SerialScene(asset)
    rows = {}
    for key, points in data['views'].items():
        P = np.array(cameras[key])@np.linalg.inv(transform)
        inv = np.linalg.inv(P[:,:3])
        eye = -inv@P[:,3]
        results = []
        for point in points:
            hit = scene.ray(eye,inv@[*point['uv'],1],120.)
            material = hit['material'] if hit else None
            results.append({**point,'hit':hit,'matches':material==point['expected']})
        rows[key]={'eye':eye.tolist(),'count':dict(Counter(row['matches'] for row in results)),'rays':results}
    output.write_text(json.dumps({'asset':scene.asset,'views':rows},ensure_ascii=False,indent=1)+'\n')
    print(asset.name,{k:v['count']for k,v in rows.items()})


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('asset',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--local',action='store_true')
    args=parser.parse_args()
    verify(args.asset,args.output,args.local)
