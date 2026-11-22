"""Check actual gate sections, colours of sampled street-wall courses, and independent sign positions."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
import gate_masonry as gate
from glb_triangles import SerialScene

def inspect(mesh):
    scene=SerialScene(mesh);physical=[];photo=[]
    def run(dest,kind,origin,direction,length,expect,lookup=None,**fields):
        hit=scene.ray(np.asarray(origin,float),np.asarray(direction,float),length,lookup)
        actual=hit['material']if hit else None
        dest.append(dict(feature=kind,expected=expect,first_surface=actual,passed=actual in expect,**fields))
    def street(feature,x,z,expected,front=-1.5,back=1.15,lookup=None):
        run(physical,feature,(x,front,z),(0,1,0),back-front,expected,lookup,x=x,z=z)
    for i,(lo,hi)in enumerate(gate.LAYOUT['east_brick']['red_intervals_m']):
        for x in [-5.15,-4.87,-2.83]:
            street('red band %d'%(i+1),x,(lo+hi)/2,[gate.RED])
            if i:
                pre=gate.LAYOUT['east_brick']['red_intervals_m'][i-1][1]
                street('grey between bands',x,(pre+lo)/2,[gate.GREY])
    for x in [-1.54,-1.11,-.43,.07,.72,1.49,1.79]:
        z=9.26 if -.78<x<1.22 else 8.60
        street('above crown',x,z+.09,[None]);street('moulded coping',x,z-.032,[gate.STONE])
        street('stepped fascia',x,z-.175,[gate.PLASTER,gate.REVEAL])
    masonry={gate.GREY,gate.RED,gate.PLASTER,gate.PIER,gate.GALLERY,gate.REVEAL}
    for k,a in gate.OPENINGS.items():
        xl,xr=a['x'];lo,hi=a['z']
        for tx,tz in [(.24,.36),(.72,.53)]:
            street('cut wall behind '+k,xl+(xr-xl)*tx,lo+(hi-lo)*tz,[None],lookup=masonry.__contains__)
    for x in [2.62,2.89,5.91,6.16]:
        street('grey side plate between transom and apron',x,5.82,[gate.GALLERY])
        street('gallery apron and folded seams',x,4.30,[gate.GALLERY,gate.METAL])
    for y in [.57,1.32,2.69]:
        for direction in [[-1,0,0],[1,0,0],[0,0,1]]:
            run(physical,'entrance passage interior section',(0,y,1.4),direction,3.,[gate.REVEAL],position_y=y)
    for x in [-1.03,-.38,.63,1.10]:
        run(physical,'open longitudinal section',(x,.55,1.6),(0,1,0),4.9,[None],position_x=x)
    for y in [.28,1.21,3.65]:
        run(physical,'photographed entrance floor',(.53,y,.68),(0,0,-1),1.,[gate.PAVING],position_y=y)
    for x in [-.67,-.53,-.41]:
        run(physical,'panel set into the visible paving',(x,2.08,.60),(0,0,-1),.9,[gate.COVER,gate.COVER_RIB],position_x=x)
    street('enamel street address',-.10,3.64,[gate.NUMBER])
    cams=json.loads((HERE/'gate-camera-registration.json').read_text())['views']
    rows=json.loads((HERE/'measured-street-pixels.json').read_text())['points']
    classes={'red band':[gate.RED],'grey masonry':[gate.GREY],'green address plate':[gate.NUMBER]}
    for point in rows:
        k=point['camera'];A=np.asarray(cams[k]['xyz_to_image']);eye=np.linalg.solve(A[:,:3],-A[:,3]);direction=np.linalg.solve(A[:,:3],[*point['uv'],1.]);direction/=np.linalg.norm(direction)
        run(photo,point['feature'],eye,direction,45,classes[point['feature']],camera=k,uv=point['uv'])
    def report(rows):
        count=sum(v['passed']for v in rows)
        return dict(passed=count==len(rows),count=count,total=len(rows),samples=rows)
    first,second=report(physical),report(photo)
    return dict(mesh=mesh.name,sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),triangles=len(scene.tri),passed=first['passed'],physical=first,photo=second)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    v=inspect(args.mesh);args.output.write_text(json.dumps(v,ensure_ascii=False,indent=1)+'\n')
    for k in ['physical','photo']:print(k,v[k]['count'],v[k]['total'],[(a['feature'],a.get('x'),a.get('z'),a['first_surface'])for a in v[k]['samples']if not a['passed']][:7])
    if not v['passed']:raise SystemExit(1)
