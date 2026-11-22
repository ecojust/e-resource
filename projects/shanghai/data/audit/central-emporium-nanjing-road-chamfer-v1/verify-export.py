"""Intersect the two folded street walls, entrance leaves, upper bays and street-number plate."""
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

AUDIT=Path(__file__).absolute().parent
PROJECT=next(p for p in AUDIT.parents if (p/'tools/package_architectural_model.py').is_file())
SOURCE=PROJECT/'source/precise/huangpu-central-emporium-nanjing-road-chamfer'
MEASUREMENTS=SOURCE/'measurements'
sys.path.insert(0,str(SOURCE/'source'))
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from market_front import GLASS,FRAME,TRIM,SHOP,BRONZE,HALF
from material_names import MATERIAL
from photo_plane import position
inspect=runpy.run_path(PROJECT/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def probes():
    out=[]
    def ray(name,base,outward,inset,material):
        outward=np.asarray(outward)
        out.append(dict(name=name,origin=(np.asarray(base)+1.5*outward).tolist(),direction=(-outward).tolist(),
                        length=2.5,range_m=[float(1.5+inset-.006),float(1.5+inset+.006)],allowed=[material]))
    def front(name,x,z,inset,mat):
        ray(name,[x,0.,z],[0,-1,0],inset,mat)
    for w in json.loads((MEASUREMENTS/'2019-upper-frontage.json').read_text())['windows']:
        shape=Polygon(w['xz']);x0,z0,x1,z1=shape.bounds
        x=(x0+x1)/2;z=(z0+z1)/2
        name=f"{w['floor']} bay {w['column']}"
        front(name+' glazing',x0+.285*(x1-x0),z,.252,GLASS)
        front(name+' projected sill',x,z0-.037,-.077,TRIM)
        front(name+' centre mullion',x,z,.188,FRAME)
    for label,a,b in [('west',(-5.27,1.23),(-HALF,0.)),('east',(HALF,0.),(5.32,1.28))]:
        a,b=np.array(a),np.array(b);t=(b-a)/np.linalg.norm(b-a);normal=[t[1],-t[0],0.];cent=(a+b)/2
        rooms=[(0.,3.25,np.linalg.norm(b-a)-.69),(4.86,7.27,.73),(8.12,9.59,.76),(11.05,12.58,.76),(15.01,17.62,.82)]
        for i,(bottom,top,width) in enumerate(rooms):
            for what,u,z,depth,m in [('glass',-.235*width,(bottom+top)/2,.252,GLASS if i else SHOP),
                                      ('mullion',0.,(bottom+top)/2,.188,FRAME if i else BRONZE),
                                      ('return wall',.5*width+.29,(bottom+top)/2,0.,MATERIAL)]:
                base=[*(cent+t*u),z]
                ray(f'{label} return {i+1} {what}',base,normal,depth,m)
    plaque=json.loads((MEASUREMENTS/'nanjing-123-plaque.json').read_text())
    for dot in plaque['fastenings']:
        x,y,z=position(*dot['center'],-.1318);front('brass fastening '+str(len(out)),x,z,y,'Aged brass fastenings')
    for row in plaque['lettering']:
        forms=[unary_union([Polygon(rings[0],rings[1:])for rings in row[k]])for k in ('lod','full')]
        witness=forms[0].intersection(forms[1]).buffer(-.85).representative_point()
        x,y,z=position(witness.x,witness.y,-.1306)
        front('123 East Nanjing Road '+row['glyph'],x,z,y,'Dark bronze plaque lettering')
    # The previous frontal render showed the background directly through
    # the fanlight rebates and beside the shopfront. Retest those same image
    # coordinates on every export before packaging.
    from corner_fanlight import STEEL,GLASS as FAN_GLASS
    from market_front import RECESS,REVEAL
    cam=next(c for c in json.loads((SOURCE/'source/cameras.json').read_bytes()) if c['name']=='script')
    eye=np.array(cam['eye']);delta=np.array(cam['target'])-eye;length=np.linalg.norm(delta)
    forward=delta/length;right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right);up=np.cross(right,forward)
    scale=length*cam['width']/cam['width_m']
    apertures=[(315,41),(315,73),(315,101),(315,143),(315,167),(427,64),(408,82),(392,100),
               (374,118),(347,148),(334,158),(270,179),(201,179),(110,180),(458,177),(530,176)]
    doorway=[(573,391),(573,443),(572,493),(571,539),(572,551),(105,484),(106,487),(106,493),(108,495)]
    for n,(col,row) in enumerate(apertures+doorway):
        direction=forward+(col+.5-cam['width']/2)*right/scale-(row+.5-cam['height']/2)*up/scale
        direction/=np.linalg.norm(direction)
        materials=[FAN_GLASS,STEEL]if n<len(apertures)else[SHOP,RECESS,REVEAL,BRONZE,MATERIAL]
        out.append(dict(name=f'visible rebate closure {col} {row}',origin=eye.tolist(),direction=direction.tolist(),
                        length=24.,range_m=None,allowed=materials))
    return out

if __name__=='__main__':
    paths=list(map(Path,sys.argv[1:]))
    roles=['raw','full','lod']if len(paths)==4 else ['model']
    cases=probes()
    results={key:inspect(p,cases)for key,p in zip(roles,paths[:-1])}
    paths[-1].write_text(json.dumps(results,ensure_ascii=False,indent=1)+'\n')
    failed={role:[(r['name'],r['first_hit'])for r in result['cases']if not r['passed']]for role,result in results.items()}
    print(len(cases),failed,flush=True)
    sys.exit(int(any(failed.values())))
