"""Independent source-pixel checks of the cropped west facade, gable and rising red eave."""
import argparse
import hashlib
import json
from math import hypot
from pathlib import Path
import runpy
import numpy as np
from register_court import Camera
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py').exists())
GLASS='Yihe | west cool reflected glass';WOOD='Yihe | west painted wood casements'
WALL='Yihe | buff courtyard masonry';EDGE='Yihe | weathered pale coping'
GABLE='Yihe | pale triangular pediment';FASCIA='Yihe | oxblood eave board'
ROOF=['Yihe | fired terracotta tile','Yihe | clay tile nose',FASCIA]
MARKS={
    'commons':[('pale face below eastern rake',451,75,[GABLE],5),('pale face below western rake',430,69,[GABLE],5),
               ('red eastern gable edge',483,81,ROOF,5),('southwest roof edge',380,83,ROOF,5),
               ('midspan roof edge',579,148,ROOF,5),('eastern roof edge',775,214,ROOF,5),
               ('first upper west sash',258,164,[GLASS,WOOD],5),('second upper west sash',230,165,[GLASS,WOOD],5),
               ('west return jamb between windows',244,168,[WALL,EDGE],5),('short glazed return',240,293,[GLASS,WOOD],5)],
    '05':[('short return upper red light',100,74,[GLASS,WOOD],5),('short return lower light',100,142,[GLASS,WOOD],5),
          ('roughcast cheek below dentils',114,42,[WALL,EDGE],5),('rising red edge toward east',532,61,ROOF,5),
          ('red tile edge near northeast corner',614,119,ROOF,5)],
    '10':[('far pale gable face',322,51,[GABLE],5),('far eastern gable rake',346,55,ROOF,5),
          ('northwestern tile edge',375,84,ROOF,5),('eastern clay edge',521,134,ROOF,5)]}

def inspect(mesh):
    api=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    scene=api['SerialScene'](mesh);rows=[]
    for v,marks in MARKS.items():
        cam=Camera(v)
        for name,x,y,mats,radius in marks:
            initial=None;closest=None
            for d,dx,dy in sorted((hypot(i,j),i,j)for i in range(-radius,radius+1)for j in range(-radius,radius+1)if hypot(i,j)<=radius):
                hit=scene.ray(cam.c,cam.ray((x+dx,y+dy)),130)
                if d==0:initial=hit
                if hit and hit['material']in mats:
                    closest=dict(offset_px=[dx,dy],radius_px=d,hit=hit);break
            rows.append(dict(photo=v,feature=name,pixel=[x,y],materials=mats,first=initial,nearest=closest))
    return dict(mesh_sha256=hashlib.sha256(mesh.read_bytes()).hexdigest(),rows=rows,total=len(rows),
                exact=sum(r['first']is not None and r['first']['material']in r['materials'] for r in rows),
                within=sum(r['nearest']is not None for r in rows))
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('report',type=Path)
    a=cli.parse_args();v=inspect(a.mesh);a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(v,indent=2)+'\n');print(v['exact'],v['within'],v['total'])
