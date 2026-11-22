"""First-surface checks across four rows, the column plinths, porch and two street doors."""
import json
from pathlib import Path
import runpy
import sys

import numpy as np

AUDIT=Path(__file__).absolute().parent
PROJECT=AUDIT.parents[2]
SRC=PROJECT/'source/precise/huangpu-chung-foo-union-bank-dianchi-front'
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0,str(SRC/'source'))
from bank_elevation import windows,observe,GLASS,IRON,LIMESTONE,DARKGLASS,BRONZE,GRANITE
from material_names import MATERIAL
from photo_plane import position
from ionic_portico import STONE
inspect=runpy.run_path(PROJECT/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def cases():
    out=[]
    def sample(name,x,z,lo,hi,materials,origin=-8.):
        out.append(dict(name=name,origin=[x,origin,z],direction=[0,1,0],length=12.,range_m=[lo-origin,hi-origin],allowed=materials))
    for (level,bay),hole in windows().items():
        a,b,c,d=hole.bounds
        label='sash '+str(level)+'-'+str(bay)
        sample(label+' glass',a+.17*(c-a),b+.45*(d-b),.126,.132,[GLASS])
        sample(label+' transom',a+.20*(c-a),b+(.62 if level==4 else .72)*(d-b),.061,.065,[IRON])
        if level==4 and bay in (1,8,9):
            sample(label+' cornice below sill',a+.48*(c-a),b-.052,-.353,-.346,[LIMESTONE])
        else:
            sample(label+' sill',a+.48*(c-a),b-.052,-.099,-.092,[LIMESTONE])
    axes=json.loads((SRC/'measurements/fluted-shafts.json').read_bytes())['columns']
    for column in axes:
        x,y,radius=column['shaft_xyr_m']
        # Compare the three measured shaft levels to the two-photo axis,
        # allowing the observed wall taper and the flute's concave groove.
        for z in [2.24,3.51,5.42]:
            sample('shaft '+str(column['index'])+' Z '+str(z),x,z,
                   y-radius*1.11,y-radius*.915,[STONE])
    for i,x in enumerate([-4.15,-1.52,6.69,9.34]):
        sample('plinth '+str(i+1),x,.22,-5.19,-5.15,[GRANITE])
    for x,y in [(2.42,-4.73),(3.19,-4.46),(3.85,-4.18),(1.93,-3.91)]:
        out.append(dict(name='entrance tread '+str(x),origin=[x,y,1.8],direction=[0,0,-1],length=2.,range_m=None,allowed=[GRANITE,LIMESTONE]))
    right=json.loads((SRC/'measurements/north-wall-openings.json').read_bytes())['west_side']
    a,b,c,d=observe(right['transom'],-4.5,'wide').bounds
    sample('western high light',a+(c-a)*.42,b+(d-b)*.34,-4.34,-4.28,[DARKGLASS])
    return out

if __name__=='__main__':
    frames=list(map(Path,sys.argv[1:]))
    probes=cases()
    names=['raw','full','lod'] if len(frames)==4 else ['model']
    out={name:inspect(path,probes)for name,path in zip(names,frames[:-1])}
    frames[-1].write_text(json.dumps(out,ensure_ascii=False,indent=1)+'\n')
    failures={n:[(q['name'],q['first_hit'])for q in role['cases']if not q['passed']]for n,role in out.items()}
    print(len(probes),failures)
    sys.exit(int(any(failures.values())))
