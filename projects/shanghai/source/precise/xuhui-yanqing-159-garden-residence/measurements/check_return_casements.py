"""Trace the four projecting steel leaves from the unwarped reference photograph."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
sys.path.insert(0,str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from upper_sash import GREEN,LIGHT,GREEN_GLASS,LIGHT_GLASS


def check(path,control,metric_scale=1.):
    scene=SerialScene(path);P=np.array(control['projection_xyz_to_pixels']);P[:,3]*=metric_scale
    inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3];rows=[]
    for name,groups in control['material_samples'].items():
        for label,samples in groups.items():
            pale=name=='attic-pale'
            expected=(LIGHT if pale else GREEN) if label=='frame' else (LIGHT_GLASS if pale else GREEN_GLASS)
            for x,y in samples:
                hit=scene.ray(eye,inv@[x,y,1.],100);actual=hit['material'] if hit else None
                rows.append(dict(group=name,pixel=[x,y],expected=expected,actual=actual,match=actual==expected))
    return dict(asset=scene.asset,metric_scale=metric_scale,samples=len(rows),matched=sum(v['match']for v in rows),readings=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--unscaled-component',action='store_true');a=p.parse_args()
    from build_model import METRIC_SCALE
    q=check(a.mesh,json.loads((HERE/'return-casement-photo-control.json').read_text()),1. if a.unscaled_component else METRIC_SCALE);a.output.write_text(json.dumps(q,indent=2)+'\n');print(q['matched'],'/',q['samples'])
