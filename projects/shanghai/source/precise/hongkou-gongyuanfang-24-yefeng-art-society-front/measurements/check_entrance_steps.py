"""Read mesh surfaces at source-image pixels independently of the stair fit."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

MEASUREMENTS=Path(__file__).resolve().parent
sys.path.insert(0,str(MEASUREMENTS.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

P=np.asarray(json.loads((MEASUREMENTS/'press-entrance-camera.json').read_bytes())['press'])
EYE=np.linalg.solve(P[:,:3],-P[:,3])
TREAD='Yefeng entrance | worn stone tread'
RISER='Yefeng entrance | dark recessed riser'
RAMP='Yefeng entrance | worn wheel strip'
LANE='Yefeng entrance | mottled road surface'
POINTS={
    TREAD:[(168,606),(172,654),(293,626),(187,714),(330,666),(220,773),(375,705)],
    RISER:[(162,628),(186,680),(200,748)],
    RAMP:[(222,615),(257,652),(300,695),(348,747),(386,777)],
    LANE:[(443,764),(438,773),(465,783)]}
def inspect(path):
    scene=SerialScene(path)
    rows=[]
    for expected,points in POINTS.items():
        for uv in points:
            ray=np.linalg.solve(P[:,:3],np.r_[uv,1.]);hit=scene.ray(EYE,ray,18)
            actual=hit['material'] if hit else None
            rows.append(dict(point=uv,expected=expected,first_surface=actual,passed=actual==expected))
    return dict(asset=scene.asset,tests=rows,passed=sum(row['passed'] for row in rows),total=len(rows))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mesh',nargs='+',type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();rows=[inspect(p) for p in args.mesh]
    args.output.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    for row in rows:print(row['asset']['file'],row['passed'],row['total'],[(r['point'],r['first_surface']) for r in row['tests'] if not r['passed']])
    if not all(row['passed']==row['total'] for row in rows):raise SystemExit(1)
