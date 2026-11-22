"""Verify the street shop bays, both rows of front windows, the rounded corner and the six windows below the fluted stone heads."""
import json
from pathlib import Path
import runpy
import sys

import numpy as np

AUDIT=Path(__file__).absolute().parent
PROJECT=AUDIT.parents[2]
SRC=PROJECT/'source/precise/huangpu-old-jiefu-nanjing-road-shopfront/source'
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0,str(SRC))
from street_path import xyz,station
from corner_crown import stone_head_sections
from nanjing_steel_windows import GLASS,TRANSOM,STEEL
from shopfront import openings,SHOP_GLASS,STONE,IRON,DISPLAY,CANOPY
inspect=runpy.run_path(PROJECT/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def cases():
    probes=[]
    def shot(label,s,z,material,depth,tolerance=.012):
        outside=station(s)[2]
        probes.append(dict(name=label,origin=xyz(s,z,1.).tolist(),direction=[-outside[0],-outside[1],0],
                           length=2.5,range_m=[1.-depth-tolerance,1.-depth+tolerance],allowed=[material]))
    # Independent observations cover the ground glazing, the upper transom light
    # and the iron fascia, as well as the continuous mouldings across the corner.
    for i,s in enumerate([-41.2,-33.8,-27.0,-19.3,-12.6,-5.5,.4,4.3,9.7,15.,22.,29.,35.8,42.7,48.],1):
        for z,mat,d,text in [(2.4,SHOP_GLASS,-.477,'lower window'),(6.1,SHOP_GLASS,-.325,'upper pane'),
                             (4.93,IRON,.084,'iron band'),(8.92,STONE,.58,'cornice')]:
            shot(f'Shop bay {i} {text}',s,z,mat,d,.055 if text=='iron band' else .012)
    for s in (36.,43.):
        shot(f'West street door stile {s}',s,2.4,CANOPY,-.42)
        shot(f'West street transom stile {s}',s,6.1,CANOPY,-.282)
    for i,(s,w) in enumerate(openings()):
        if i%3!=0 or -3.5<s<13.:continue
        # All surveyed ordinary second- to fourth-row openings have the same
        # paired leaves and narrow transom. Use three different heights and
        # compare centre stiles to inset neighbouring glass.
        for floor,(base,h) in enumerate([(14.50,3.45),(18.10,3.04),(21.22,3.43)],2):
            for u,v,mat,d,text in [(.23,.74,GLASS,-.403,'glass'),(.28,.95,TRANSOM,-.422,'transom')]:
                shot(f'Opening {i+1} row {floor} {text}',s+(u-.5)*w,base+v*h,mat,d)
    for i,section in enumerate(stone_head_sections(),1):
        fraction=.915 if i==4 else .27
        s=float(section[0,0]*(1-fraction)+section[-1,0]*fraction)
        z=float(np.interp(s,section[:,0],section[:,1]))
        shot(f'Upper return {i} pane',s,z-.19,GLASS,-.387,.019)
        shot(f'Upper return {i} transom',s,z-.30,IRON,-.301,.019)
    for s in [3.8,5.5,7.4]:
        shot(f'Display fixing plane {s}',s,15.6,DISPLAY,.191)
    return probes

if __name__=='__main__':
    inputs=list(map(Path,sys.argv[1:]));probes=cases()
    roles=['raw','full','lod'] if len(inputs)==4 else ['model']
    results={role:inspect(path,probes)for role,path in zip(roles,inputs[:-1])}
    inputs[-1].write_text(json.dumps(results,ensure_ascii=False,indent=1)+'\n')
    failures={k:[(p['name'],p['first_hit'])for p in r['cases']if not p['passed']] for k,r in results.items()}
    print(len(probes),failures)
    sys.exit(int(any(failures.values())))
