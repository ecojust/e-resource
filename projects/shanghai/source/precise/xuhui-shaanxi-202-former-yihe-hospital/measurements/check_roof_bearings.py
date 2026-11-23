"""Verify the continuous soffit and its supporting walls on a set of measured building sections."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from shapely.geometry import box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').is_file())
WINDOW_WALL='Yihe | buff courtyard masonry'
INDICATIVE='Yihe | muted rear massing'
SOFFIT='Yihe | weathered pale coping'

def inspect(mesh):
    api=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    scene=api['SerialScene'](mesh)
    data=json.loads((HERE/'roof-and-wing-evidence.json').read_bytes())
    footprint=unary_union([box(*b)for b in data['hip_rectangle_bounds_m']])
    body=orient(footprint.buffer(-.32,join_style=2),sign=1)
    controls=[]
    def add(group,origin,direction,length,material):
        hit=scene.ray(np.asarray(origin),np.array(direction,dtype=float),length)
        controls.append(dict(section=group,origin_m=list(origin),direction=list(direction),limit_m=length,
                             expected=material,first=hit,pass_check=hit is not None and hit['material']==material))
    coords=list(body.exterior.coords)
    for i,(start,end)in enumerate(zip(coords,coords[1:])):
        a=np.array(start);b=np.array(end);t=b-a;L=np.linalg.norm(t);n=np.array([t[1],-t[0]])/L
        if L<.18:continue
        for step in ((.25,.5,.75)if L>3 else (.5,)):
            xy=a+step*t
            # Each external roof lip, including the photographed bay, must have a soffit immediately above.
            if xy[1]<.20:continue
            add('soffit under perimeter '+str(i),[*list(xy+n*.11),15.015],[0,0,1],.2,SOFFIT)
            if abs(xy[0]+10.43)<.17 and xy[1]<8.23:continue
            for height in (2.1,8.8,14.86):
                add('body under roof '+str(i),[*list(xy+n*.09),height],[*list(-n),0],.23,INDICATIVE)
    # The two measured, decorated side faces remain open to the courtyard. The surrounding massing may not obscure them.
    for x,y in [(-9.25,0),(-6.9,0),(-3.85,0),(3.5,0),(9.35,0)]:
        add('court bearing', [x,y-.025,15.02],[0,0,1],.19,SOFFIT)
        add('masonry top under fascia',[x,y+.06,15.14],[0,0,-1],.15,WINDOW_WALL)
    return dict(asset_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),passes=sum(v['pass_check']for v in controls),
                total=len(controls),checks=controls)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('report',type=Path)
    a=cli.parse_args();result=inspect(a.mesh);a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n');print(result['passes'],result['total'])
