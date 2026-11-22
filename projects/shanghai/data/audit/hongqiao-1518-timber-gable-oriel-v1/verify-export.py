"""Intersect serialized meshes with garden-photo rays and metric probes for window reveals."""
from pathlib import Path
import json, runpy, sys

import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE.parents[2]/'source/precise/changning-hongqiao-1518-timber-gable-oriel'
INSPECT=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']
C=json.loads((SRC/'measurements/garden-camera.json').read_bytes())
P=np.array(C['pinhole_3x4']);EYE=C['eye_xyz'];INV=np.linalg.inv(P[:,:3])
ROOF=['480 terracotta pan tile','480 sun-warmed burnt clay','480 weathered brown pan','480 deep clay lap and exposed lower edge','480 curved terracotta hip cap','480 shadowed rim of overlapping cap']
GLASS=['Dark garden glass','Garden glass pale reflection','Garden glass shadow']
TIMBER='Dark exposed garden timbers'; SASH='Deep brown painted window sash'
STONE='Cream dressed stone sill';CREAM='Cream mineral roughcast'

def cases():
    rows=[]
    def add(n,p,d,l,allow=None,interval=None):
        rows.append(dict(name=n,origin=list(p),direction=list(d),length=l,allowed=allow,range_m=interval))
    def photo(n,u,v,allow):
        d=INV@[u,v,1.];add(n,EYE,d/np.linalg.norm(d),39.,allow)
    h=C['fitted_glass_height_m'];pitch=C['nominal_spacing_m']
    for i in range(4):
        x=(i-1.5)*pitch
        for j,k in enumerate([.16,.40,.64,.86]):
            add(f'attic recessed pane {i+1} sample {j+1}',[x,-.20,h*k],[0,1,0],.37,
                [['Blue reflected attic glass','Cool reflected attic glass'][i%2]],[.260,.264])
        for sign in [-1,1]:
            add(f'attic glass bead {i+1} side {sign}',[x+sign*(C['nominal_glass_width_m']/2+.007),-.2,.5*h],[0,1,0],.32,
                ['Light on the joinery bead'],[.201,.206])
    for i,x in enumerate([523.4,540.8,560.2,581.5,601.2],1):
        for j,y in enumerate([365.6,385.8,407.6],1):photo(f'ground bow {i} light {j}',x,y,GLASS)
    for i,x in enumerate([530.8,550.7,569.7,593.8],1):
        for j,y in enumerate([248.,274.,285.]):photo(f'oriel light {i} sample {j}',x,y,GLASS)
    for i,(x,y) in enumerate([(559,306),(565,313),(549,314),(559.4,315.3),(592,306),(595.0,304.8)],1):
        photo(f'oriel carved apron {i}',x,y,['Pale stone on the apron ribbons','Recessed cream apron panels'])
    for n,xrange,yrange in [('gable', [553,562,572,578,583], [93,99]),('oriel',[545,551,560,569,576],[187,191,196])]:
        for x in xrange:
            for y in yrange:photo(f'{n} roof tile {x}/{y}',x,y,ROOF)
    for i,(x,y) in enumerate([(517,146),(488,190),(619,152),(638,190),(522,175),(630,200)],1):
        photo(f'garden timberwork {i}',x,y,[TIMBER])
    for i,(x,y) in enumerate([(543,329),(546,335),(571,329),(574,335)],1):
        photo(f'two oriel consoles {i}',x,y,[STONE])
    for i,(x,y) in enumerate([(460,140),(485,143),(642,120),(669,133),(553,65),(592,71)],1):
        photo(f'open sky outside shaped verge {i}',x,y,None)
    return rows

if __name__=='__main__':
    args=list(map(Path,sys.argv[1:]));roles=['raw','full','lod'] if len(args)==4 else ['model'];assert len(args)==len(roles)+1
    result={k:INSPECT(f,cases())for k,f in zip(roles,args)}
    args[-1].write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    for k,s in result.items():
        print(k,len(s['cases']),[(p['name'],p['first_hit'] and p['first_hit']['material'])for p in s['cases']if not p['passed']])
    sys.exit(int(not all(x['passed']for x in result.values())))
