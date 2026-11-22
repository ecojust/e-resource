"""Inspect unfiltered material intersections through the two photographed gate leaves."""
from pathlib import Path
import argparse
import json
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from garden_gate_leaves import DATA,SKIN,EDGE,IRON,GLASS,SCREEN,LOCK,BOSS,SLOT,STONE
from guanghua_gate_camera import camera_matrix

def check(asset):
    scene=SerialScene(asset); results=[]
    def cast(label,start,direction,limit,expected,**meta):
        hit=scene.ray(start,direction,limit)
        material=hit['material'] if hit else None
        results.append(dict(label=label,passed=material in expected,expected=expected,first_material=material,**meta))
    def front(label,x,z,expected):
        cast(label,[x,-.28,z],[0,1,0],.89,expected,world_xz=[x,z])
    for row in DATA['clear_openings']:
        name=row['leaf'];l,lo,r,hi=row['clear_opening_xz']
        def x(p):return l+(p-25)*(r-l)/182
        def z(p):return hi-(p-66)*(hi-lo)/287
        for px in [76,160]:
            for py in [90,181,249,328]:front(name+' upright',x(px),z(py),[IRON])
        for py in [132,287]:
            for px in [41,106,135,192]:front(name+' full crosspiece',x(px),z(py),[IRON])
        for py in [115,149,208,270,304]:
            for px in [42,173]:front(name+' half-width crosspiece',x(px),z(py),[IRON])
            front(name+' open centre between short irons',x(113),z(py),[GLASS,SCREEN])
        for px in [53,182]:
            for py in [123,141,279,298]:front(name+' short upright at decorative return',x(px),z(py),[IRON])
        for px in [36,98,144,191]:
            for py in [82,167,229,339]:front(name+' screen behind ironwork',x(px),z(py),[GLASS,SCREEN])
        for edge in (l,r):
            for f in [.1,.5,.89]:front(name+' folded jamb',edge+(-.004 if edge==l else .004),lo+(hi-lo)*f,[EDGE])
        front(name+' upper weather hood',(l+r)/2,hi+.011,[EDGE])
        front(name+' lower frame',(l+r)/2,lo,[EDGE])
        for f in [.16,.39,.67,.90]:front(name+' solid metal face',(l+r)/2,lo*f,[SKIN])
    for key,material in [('upper_lock_xz',LOCK),('lower_spindle_xz',BOSS)]:
        front(key,*DATA['review_locks_and_slot'][key],[material])
    l,lo,r,hi=DATA['review_locks_and_slot']['slot_xz']
    for f in [.13,.53,.88]:front('letter delivery slot',l+(r-l)*f,(lo+hi)/2,[SLOT])
    for x in [-.52,-.28,0,.31,.55]:cast('grey single threshold',[x,.12,.36],[0,0,-1],.4,[STONE])
    hand={'gao05':[(408,263,LOCK),(406,297,BOSS),(365,187,GLASS),(471,205,GLASS),(391,281,SLOT),(462,365,SKIN)],
          'yan04':[(1475,2309,LOCK),(1467,2507,BOSS),(1777,1896,GLASS)]}
    # Preserve the photographed control pixel for every ray, including any genuine conflict.
    for key,pixels in hand.items():
        P=camera_matrix(key);c=-np.linalg.solve(P[:,:3],P[:,3])
        for u,v,mat in pixels:
            options=[mat] if mat!=GLASS else [GLASS,SCREEN]
            cast(key+' original photograph',c,np.linalg.solve(P[:,:3],[u,v,1]),15,options,pixel=[u,v])
    return dict(**scene.asset,count=len(results),passed=all(t['passed']for t in results),checks=results)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('asset',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    doc=check(args.asset);args.output.write_text(json.dumps(doc,indent=1)+'\n')
    failed=[(w['label'],w.get('pixel') or w.get('world_xz'),w['first_material']) for w in doc['checks'] if not w['passed']]
    print(doc['count']-len(failed),doc['count'],failed);sys.exit(bool(failed))
