"""Audit the signed GLBs at the measured arch, paired window sashes and recessed doorway."""
import argparse
import json
import math
import runpy
from pathlib import Path

HERE=Path(__file__).absolute().parent
SOURCE=HERE.parents[2]/'source/precise/hongkou-huayuanli-six-court-arch'
D=json.loads((SOURCE/'source/dimensions.json').read_bytes())
OBS=json.loads((SOURCE/'measurements/plate-725.json').read_bytes())
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def cases():
    rows=[]
    def add(name,origin,ray,allowed,interval,length):
        rows.append(dict(name=name,origin=origin,direction=ray,allowed=[allowed] if isinstance(allowed,str) else allowed,range_m=interval,length=length))
    def front(name,x,z,material,lo=None,hi=None,maximum=3.4):
        add(name,[x,-1.85,z],[0,1,0],material,[lo,hi] if lo is not None else None,maximum)
    def down(name,x,y,z,material,base=3.5,tolerance=.012):
        add(name,[x,y,base],[0,0,-1],material,[base-z-tolerance,base-z+tolerance],base+.2)
    crown=D['arch_center_z']+D['arch_radius'];radius=D['arch_radius']
    for i,(x,z) in enumerate(OBS['arch_edge_on_assumed_plane_m']):
        front('Measured inner arch from plate 725, solid '+str(i),x,z+.032,'Buff lime finish',1.40,1.43)
        front('Clear space directly below measured arch '+str(i),x,z-.035,None,maximum=1.61)
    for i,x in enumerate([-1.13,-.88,-.62,-.34,-.11,.18,.42,.67,.89,1.13]):
        cap=D['porch_cap_crown']-1.96+math.sqrt(1.96**2-(x-D['arch_center_x'])**2)
        edge=D['arch_center_z']+math.sqrt(radius**2-(x-D['arch_center_x'])**2)
        front('Arc face '+str(i),x,(cap+edge)/2,'Buff lime finish',1.40,1.43)
        front('Coping projecting drip '+str(i),x,cap-.044,'Rounded light drip',1.28,1.33)
        down('Coping weather surface '+str(i),x,-.46,cap+.001,'Pale cast coping',tolerance=.024)
    for x in(-1.44,1.44):
        for z in(.32,1.,1.7):front(f'Arch outer pier {x} {z}',x,z,'Buff lime finish',1.40,1.43)
    for x in(-1.50,-.94,.94,1.50):
        for z in(3.48,4.16,5.30):front(f'Upper roughcast {x} {z}',x,z,'Huayuanli grey roughcast',1.94,1.99)
    wx=D['upper_center'];w=D['upper_frame_width'];leaf=(w-2*.069-.018)/2
    zs=[D['upper_frame_sill']+.074+.078,*D['upper_dividers_z'],D['upper_frame_top']-.068-.07]
    for i,side in enumerate((-1,1)):
        x=wx+side*(leaf+.018)/2
        for k,(lo,hi) in enumerate(zip(zs,zs[1:])):
            for offset in(-.105,.105):
                front(f'Casement {i+1} glass {k+1} at {offset}',x+offset,(lo+hi)/2,
                      'Smoky teal glazing' if (k+i)%3 else 'Pale grey green glazing',2.032,2.046)
            # Probe a genuinely distinct, narrow strip of actual putty around each pane.
            front(f'Casement {i+1} light {k+1} putty',x-leaf/2+.055+.006,(lo+hi)/2,'Brown linseed putty',2.012,2.026)
        for k,z in enumerate(D['upper_dividers_z']):
            front(f'Casement {i+1} sash rail {k+1}',x,z,'Oxide red painted joinery',1.97,2.00)
    front('Central joint between separate casements',wx,4.58,'Recess at frame',2.056,2.08)
    for x in(-.59,.58):
        down(f'Stone sill {x}',x,-.11,D['upper_frame_sill']-.032,'Grey sill stone',base=4.07,tolerance=.056)
    for x in(-.37,0.,.37):
        for z in(.49,1.10,1.67,1.99):
            front(f'Unobstructed open threshold {x} {z}',x,z,None,maximum=2.84)
            front(f'Declared rear study limit {x} {z}',x,z,'Study cut darkness',2.92,2.96)
    for side in(-1,1):
        for z in(.5,1.,1.58):
            front(f'Red recessed doorway jamb {side} {z}',side*.54,z,'Oxide red painted joinery',1.79,1.83)
    for x in(-.32,.02,.31):
        down(f'Raised threshold {x}',x,-.07,D['threshold_height'],'Grey tread',base=.95)
        down(f'Threshold outer slope {x}',x,-.22,.1032,'Grey tread',base=.9)
        for y in(-.90,-.50):down(f'Court paving {x} {y}',x,y,0.,'Grey tread',base=.9)
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for arg in ('raw','full','lod','out'):parser.add_argument(arg,type=Path)
    inp=parser.parse_args();report={role:INSPECT(getattr(inp,role),cases()) for role in ('raw','full','lod')}
    inp.out.write_text(json.dumps(report,ensure_ascii=False,separators=(',',':'))+'\n')
    for role,result in report.items():print(role,len(result['cases']),[(v['name'],v['first_hit'])for v in result['cases']if not v['passed']][:12])
    raise SystemExit(int(not all(r['passed']for r in report.values())))
