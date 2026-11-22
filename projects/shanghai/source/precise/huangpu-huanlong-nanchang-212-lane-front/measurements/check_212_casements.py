"""Read real GLB triangles and cast first-surface rays against the photographed 212 casements."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from upper_casements import openings,leaf_geometry,WOOD,FRAME,PUTTY,GLASS,STONE,SHADOW
from glb_triangles import SerialScene

def expected(low):
    up=np.array([0.,0.,1.])
    into=np.array([0.,1.,0.])
    for row in openings():
        name=row['key'];l,r,b,t=[row[k] for k in ('left','right','bottom','top')]
        for fraction in (.18,.58,.86):
            yield name+' sill',np.array([l+fraction*(r-l),-.064,b-.02]),into,STONE,.012
        for x,what in ((l+.011,'jamb'),(r-.011,'jamb'),((l+r)/2,'post')):
            y=.057 if what=='post' else .047
            yield name+' '+what,np.array([x,y,b+.26*(t-b)]),into,FRAME,.009
        # The distant shadow backing is reached through two deliberately open apertures.
        for f in (.21,.76):
            yield name+' opening beyond the open timber', np.array([l+f*(r-l),1.14,b+.62*(t-b)]),into,SHADOW,1.15
        for i in range(3):
            hinge,d,n,w,_,_=leaf_geometry(row,i)
            low_z,hi_z=b+.024,t-.022
            floor,top=low_z+.052,hi_z-.043
            tag=f'{name} sash {i+1} '
            def check(s,y,z,element,material,gap=.008):
                return tag+element,hinge+s*d+y*n+up*z,n,material,gap
            for s in (.015,w-.015):
                yield check(s,-.015,low_z+.57*(hi_z-low_z),'outside stile',WOOD)
            for s in (.25*w,.75*w):
                yield check(s,-.015,low_z+.024,'bottom rail',WOOD)
                yield check(s,-.015,hi_z-.019,'top rail',WOOD)
                for k in (1,2,3):
                    yield check(s,-.009,floor+(top-floor)*k/4,'transverse rail',WOOD)
            for k in range(4):
                z=floor+(top-floor)*(k+.5)/4
                yield check(w/2,-.009,z,'central glazing bar',WOOD)
                for p,q in ((.030,w/2-.007),(w/2+.007,w-.030)):
                    yield check((p+q)/2,-.002,z,'independent glass pane',GLASS)
                    yield check(p+.002,-.002 if low else -.006,z,'rebate or plain far pane',GLASS if low else PUTTY)
                    yield check(q-.002,-.002 if low else -.006,z,'opposite rebate or far pane',GLASS if low else PUTTY)
def inspect(model,low):
    scene=SerialScene(model);checks=[]
    for tag,p,d,mat,gap in expected(low):
        hit=scene.ray(p-d*gap,d,gap+.003)
        error=None if hit is None else float(np.linalg.norm(np.asarray(hit['point_enu_m'])-p))
        actual=None if hit is None else hit['material']
        checks.append(dict(feature=tag,expected_xyz_m=p.round(6).tolist(),direction=d.round(6).tolist(),expected_material=mat,first_material=actual,distance_error_m=error,passed=actual==mat and error is not None and error<.0017))
    return dict(**scene.asset,level='lod' if low else 'full',triangles=len(scene.tri),rays=len(checks),passed=all(r['passed'] for r in checks),checks=checks)
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('model',type=Path);parser.add_argument('level',choices=('full','lod'));parser.add_argument('output',type=Path)
    args=parser.parse_args()
    report=inspect(args.model,args.level=='lod')
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n')
    print(sum(r['passed'] for r in report['checks']),report['rays'],report['triangles'])
    raise SystemExit(0 if report['passed'] else 1)
