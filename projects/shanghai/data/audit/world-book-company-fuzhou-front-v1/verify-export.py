"""Check the first visible material on the actual Fuzhou Road shopfront meshes."""
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
SOURCE=PROJECT/'source/precise/huangpu-world-book-company-fuzhou-front/source'
sys.path.insert(0,str(SOURCE))
from fuzhou_photo_plane import on_wall
from shopfront import BRASS,CANOPY,DATA,GLASS,GRANITE,RAIL,SHOP,SOURCE as MEASURES,STONE,rect,shop_openings
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']


def observations():
    rows=[]
    def test(name,origin,direction,material,distance,epsilon):
        rows.append(dict(name=name,origin=list(origin),direction=list(direction),length=distance+epsilon+.02,
                         range_m=[distance-epsilon,distance+epsilon],allowed=[material]))
    def front(name,x,z,material,y,tol=.008):
        test(name,[x,-3.,z],[0.,1.,0.],material,y+3.,tol)
    for bay in DATA['bays']:
        l,z,r,top=rect(bay['black_fascia'],-.32).bounds
        for k in [.16,.84]:
            front(f"Dark fascia {bay['bay']}, position {k}",l+(r-l)*k,z+(top-z)*.44,GRANITE,-.38)
    for n,(bay,kind,l,z,r,top,lights) in enumerate(shop_openings(),1):
        if kind=='upper':
            for k in range(lights):
                x=l+(r-l)*(k+.5)/lights
                front(f'Bay {bay} glazed upper shopfront {k+1}',x,z+(top-z)*.55,GLASS,.424)
            for k in range(1,lights):
                x=l+(r-l)*k/lights
                front(f'Bay {bay} upper shopfront mullion {k}',x,z+(top-z)*.58,RAIL,.345)
        elif kind=='display':
            for k in [.34,.65]:
                front(f'Lower display {n}, position {k}',l+(r-l)*k,z+(top-z)*.28,SHOP,.544)
            front(f'Lower display {n} sill',(l+r)*.5,z-.07,GRANITE,-.196)
        else:
            for k in range(3):
                front(f'Recessed entrance door {k+1}',l+.06+(r-l-.12)*(k+.5)/3,z+(top-z)*.43,SHOP,1.384)
    for n,row in enumerate(DATA['stone_figures'],1):
        sec=row['body_sections_px']
        for j in (2,len(sec)//2,len(sec)-3):
            v,l,r=sec[j]
            p=on_wall((l+r)*.5,v,-.32)
            front(f'Stone figure {n} photographed profile row {j}',p[0],p[2],STONE,-.45,.27)
        v,l,r=sec[-1];q=on_wall((l+r)*.5,v,-.32)
        front(f'Pedestal of photographed figure {n}',q[0],q[2]-.057,STONE,-.67)
    for canopy in DATA['canopies']:
        left,right=[np.asarray(on_wall(*uv,-.095)) for uv in canopy['rear_edge']]
        lower_left,lower_right=[np.asarray(on_wall(*uv,-.91)) for uv in canopy['street_edge']]
        lights=canopy['visible_glass_lights']
        for k in range(lights):
            u=(k+.5)/lights
            a=(1-u)*left+u*right;b=(1-u)*lower_left+u*lower_right
            p=a*.50+b*.50
            test(f"Canopy {canopy['bay']} sloping glass sheet {k+1}",p+[0,0,.16],[0,0,-1],CANOPY,.16,.013)
    mark=json.loads((MEASURES/'visible-brass-shop-mark.json').read_bytes())
    for row in mark['strokes']:
        p=on_wall(*row['centreline_px'][len(row['centreline_px'])//2],-.4)
        front('Silvered brass script '+row['label'],p[0],p[2],BRASS,-.4,.004)
    return rows


if __name__=='__main__':
    probes=observations()
    results={role:inspect(Path(path),probes) for role,path in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    print({k:[c['name'] for c in v['cases'] if not c['passed']] for k,v in results.items()})
    raise SystemExit(0 if all(entry['passed']for entry in results.values()) else 1)
