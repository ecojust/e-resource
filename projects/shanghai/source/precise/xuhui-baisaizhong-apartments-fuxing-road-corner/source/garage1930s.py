"""Harrison Forman's two garage bays on the former Route Magy, circa 1932–37.

A separate optional streetscape component. Source photographs are not embedded.
All s values increase along the siding from the cut-corner entrance.
"""
from pathlib import Path
import argparse
import json
import numpy as np
from shapely.geometry import LineString, Polygon, box
from materials import rgb
from plan import STREETS

BOARD = 'Garage | weathered vertical boarding'
RAIL = 'Garage | pale stiles and diagonal rails'
IRON = 'Garage | upper geometric grille'
HARDWARE = 'Garage | dark iron fittings'
RECESS = 'Garage | shadow behind original leaves'
PALETTE = {BOARD: rgb((149, 143, 131)), RAIL: rgb((180, 175, 163)),
           IRON: rgb((133, 135, 127), .57), HARDWARE: rgb((67, 65, 59), .55),
           RECESS: rgb((39, 40, 38))}
BAYS = ((1.15, 3.51), (4.25, 6.62))
BOTTOM, HEAD = .035, 2.015

def wing_basis():
    a, end = STREETS['wulumuqi']
    axis = (end - a) / np.linalg.norm(end - a)
    return a, axis, np.array((axis[1], -axis[0]))

def add_historic_garage(b, lod=False):
    a, axis, outward = wing_basis()
    def solid(shape, back, front, material, name):
        def point(s, z, depth):
            xy = a + axis * s + outward * depth
            return (xy[0], xy[1], z)
        if shape.area:
            b.prism(shape, back, front, point, material, '1930s | '+name)
    def bar(coords, width, depth, mat, name):
        solid(LineString(coords).buffer(width/2, cap_style=2, join_style=2),
              depth, depth+.014, mat, name)
    def leaf(s0, s1, outer_left, offset, label):
        span = s1-s0
        def s(t): return s0 + (t if outer_left else 1-t)*span
        def diag(t): return 1.925-.53*t
        # Tall vertical boards are individually visible through the bottom field.
        n=9 if not lod else 6
        for i in range(n):
            t0=i/n+.0015; t1=(i+1)/n-.0015
            solid(Polygon([(s(t0),BOTTOM+.04),(s(t1),BOTTOM+.04),
                           (s(t1),diag(t1)),(s(t0),diag(t0))]),
                  offset,offset+.031, BOARD,label+' board '+str(i+1))
        for t in (0., .5, 1.):
            x=s(t); shift=.022 if x<=s0+.001 else (-.022 if x>=s1-.001 else 0.)
            bar(((x+shift,BOTTOM+.015),(x+shift,HEAD-.016)),.048,offset+.033,RAIL,label+' stile')
        for z in (BOTTOM+.044, HEAD-.024):
            bar(((s(0.),z),(s(1.),z)),.058,offset+.032,RAIL,label+' horizontal rail')
        bar(((s(.006),diag(.006)),(s(.994),diag(.994))),.108,offset+.037,RAIL,label+' diagonal')
        for t in (.18,.36,.66,.82):
            x=s(t); z=diag(t)+.05
            if z < HEAD-.065:
                bar(((x,z),(x,HEAD-.05)),.013,offset+.006,IRON,label+' grille upright')
        # The exposed upper half shows square-ended descending folded bars.
        for t, depth in ((.57,.138),(.76,.196)):
            u=t+.10; z=max(diag(t)+.087,HEAD-.095-depth)
            bar(((s(t),HEAD-.064),(s(t),z),(s(u),z),(s(u),HEAD-.064)),
                .014,offset+.017,IRON,label+' square drop')
        for t in (.86,.944):
            xc=s(t);z=.883 if t<.90 else .832; r=.021
            xz=[(xc+np.cos(v)*r,z+np.sin(v)*r) for v in np.linspace(0,np.pi*2,11)[:-1]]
            solid(Polygon(xz),offset+.043,offset+.062,HARDWARE,label+' fixing')
    for i,(lo,hi) in enumerate(BAYS):
        # This shallow unlit surface also masks the contemporary shop mullions
        # when the photographic variant is selected. It is behind every leaf.
        solid(box(lo-.004,.013,hi+.004,HEAD+.008),.004,.017,RECESS,'bay '+str(i+1)+' inner shadow')
    lo,hi=BAYS[0]
    # Only the paired panels left of the real person in the first opening are
    # recoverable. Leave the rest in silhouette where the street pole obscures it.
    leaf(lo,lo+.58*(hi-lo),True,.048,'near visible bank')
    lo,hi=BAYS[1]; middle=lo+(hi-lo)*.496
    leaf(lo,middle-.009,True,.055,'far left bank')
    leaf(middle+.009,hi,False,.047,'far right bank')

if __name__=='__main__':
    from build_model import PROJECT  # installs the shared architectural builder path
    from photo_architecture import Builder
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('output',type=Path);args.add_argument('--lod',action='store_true')
    cli=args.parse_args()
    b=Builder(PALETTE); add_historic_garage(b,cli.lod)
    cli.output.parent.mkdir(parents=True,exist_ok=True)
    meta={'name':'白赛仲公寓旧车库门（馆方约1932–1937年）','geometry_license':'MIT',
          'archives':'UWM AGSL Harrison Forman fr212568','photos_embedded':False,
          'coordinate_frame':'Shares the complete Boissezon model coordinates; Metres, Z up before glTF export'}
    result=b.save(cli.output,meta)
    print(json.dumps({k:result[k] for k in ('triangles','parts','sha256','bytes')}))
