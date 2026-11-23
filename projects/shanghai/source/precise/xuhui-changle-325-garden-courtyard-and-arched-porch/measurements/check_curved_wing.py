"""Test fixed garden and street image pixels against the exported first-hit triangle."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from register_court import Camera


def check(mesh):
    record=json.loads((HERE/'wing-separate-pixels.json').read_text())
    scene=SerialScene(mesh);out={}
    for k,groups in record['picks'].items():
        c=Camera(k);rows=[]
        for note,(short,pts)in groups.items():
            want=['325 garden | '+short] if short!='tile'else['325 garden | muted orange pan tile','325 garden | pale terracotta round edges']
            for p in pts:
                point=np.array(p)
                def hit(offset):
                    impact=scene.ray(c.c,c.ray(point+offset),65)
                    return impact['material']if impact else None
                m=hit([0,0]);nearest=[0,0]if m in want else None
                for r in (1,2,3,5,8):
                    if nearest is not None:break
                    a=r*c.size[0]/1050
                    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(.707,.707),(-.707,.707),(.707,-.707),(-.707,-.707)]:
                        delta=np.round([a*dx,a*dy],2)
                        if hit(delta)in want:
                            nearest=delta.tolist();break
                rows.append({'feature':note,'native_px':p,'material':want,'actual_first_material':m,'matched':m in want,'nearest_offset_native_px':nearest})
        out[k]={'observations':rows,'n':len(rows),'exact':sum(x['matched']for x in rows),'within_8px_at_1050':sum(x['nearest_offset_native_px']is not None for x in rows)}
    return {'asset':scene.asset,'camera_data_sha256':hashlib.sha256((HERE/'wing-cameras.json').read_bytes()).hexdigest(),'stations':out}


if __name__=='__main__':
    args=argparse.ArgumentParser(description=__doc__);args.add_argument('asset',type=Path);args.add_argument('output',type=Path)
    a=args.parse_args();r=check(a.asset);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    print({k:(v['exact'],v['within_8px_at_1050'],v['n'])for k,v in r['stations'].items()})
