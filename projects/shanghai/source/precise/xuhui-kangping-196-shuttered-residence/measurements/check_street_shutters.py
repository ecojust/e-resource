"""Sample photographed shutters and window frames with the 2019 camera against the published geometry."""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'source'))
sys.path.insert(0,str(ROOT.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from photo_plane import EYE, INV
from materials import WOOD, LOUVER, GLASS
from shuttered_windows import RECORD

def check(mesh):
    scene=SerialScene(mesh)
    spots={'left-window main upright':(1771,2102,[WOOD]),'right-window main upright':(3337,2077,[WOOD]),
           'door bottom dark panel':(2582,2293,[WOOD]),'door upper centre stile':(2622,1860,[WOOD]),
           'small left glass':(228,1882,[GLASS]),'small right glass':(952,1867,[GLASS])}
    for side,cols in [('wide-left',1685),('wide-right',3425)]:
        for tier,scan in enumerate(RECORD['wide_windows'][side]):
            for i,y in enumerate(scan['bright_edges_y']):
                spots[f'{side} tier {tier+1} bright edge {i+1}']=(cols,y,[LOUVER])
    for col,positions in RECORD['holdout'].items():
        for i,(x,y) in enumerate(positions):
            spots[f'held-out {col} {i+1}']=(x,y,[LOUVER])
    rows=[]
    for name,(x,y,expected) in spots.items():
        rgb=INV@np.array([x*800/3968,y*800/3968,1.])
        direction=rgb/np.linalg.norm(rgb)
        if direction[1]<0:direction=-direction
        hit=scene.ray(EYE,direction,150)
        material=hit['material'] if hit else None
        rows.append(dict(name=name,native_uv=[x,y],expected=expected,material=material,
                         point=hit['point_enu_m'] if hit else None,passed=material in expected))
    return dict(sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),samples=len(rows),
                direct_hits=sum(x['passed'] for x in rows),held_out=sum(x['name'].startswith('held-out') for x in rows),held_out_hits=sum(x['passed'] and x['name'].startswith('held-out') for x in rows),checks=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();r=check(args.mesh);args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['direct_hits'],r['samples'])
