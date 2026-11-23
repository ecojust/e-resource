"""Check photographed pixels against the actual first triangle of the address module or whole house."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').exists())
sys.path[:0]=[str(HERE.parent/'source'),str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from placement import Facade
from numbered_entrance import GREEN,IVORY,LOUVER
from materials import CEMENT,DARK,FRAME,GLASS,GRILLE,IRON,PAVE,PLASTER,SHADOW,WOOD

SAMPLES={
    'south-2015':[
      ('outer arch at crown',681,375,[CEMENT]),('outer arch left slope',496,470,[CEMENT]),('arch right slope',846,463,[CEMENT]),
      ('left cement jamb',457,706,[CEMENT]),('right cement jamb',889,682,[CEMENT]),('inner left plaster reveal',506,709,[SHADOW,PLASTER]),
      ('left timber leaf',570,609,[WOOD]),('right timber leaf',704,714,[WOOD]),('top tread',649,839,[PAVE]),('front step',716,869,[PAVE]),
      ('lower left window',359,656,[GLASS,FRAME]),('lower right window',1006,637,[GLASS,IRON,FRAME])],
    'north-2020':[
      ('cast arch outer crown',680,436,[CEMENT]),('arch left curve',549,492,[CEMENT]),('left foot of surround',508,751,[CEMENT]),
      ('deep left lining',553,668,[SHADOW,PLASTER]),('upper dark door',695,494,[WOOD]),('lower timber door',682,693,[WOOD]),
      ('threshold',672,810,[PAVE]),('green numbered plate',854,514,[GREEN,IVORY]),('cream hood top rim',937,333,[LOUVER]),
      ('middle cream blade',930,386,[LOUVER,SHADOW]),('lower cream blade',937,426,[LOUVER,SHADOW]),
      ('left low glass',445,635,[GLASS,FRAME]),('right low grille',917,667,[IRON,GLASS]),
      ('left ornamental plinth vent',404,788,[GRILLE,DARK]),('right ornamental plinth vent',936,849,[GRILLE,DARK])]}
def inspect(mesh,front_origin=(0,0),along=(0,1)):
    model=SerialScene(mesh)
    src=json.loads((HERE/'numbered-entrance-two-stations.json').read_bytes())
    facade=Facade(None,front_origin,along)
    output={}
    for station,rows in SAMPLES.items():
        p=np.array(src['stations'][station]['P_local'])
        inv=np.linalg.inv(p[:,:3]);eye=-inv@p[:,3];origin=np.array(facade.point(*eye));hits=[]
        for label,u,v,mat in rows:
            target=np.array(facade.point(*(eye+inv@[u,v,1])))
            hit=model.ray(origin,target-origin,70)
            hits.append({'feature':label,'source_pixel':[u,v],'expected':mat,'hit':hit,'matched':bool(hit and hit['material'] in mat)})
        output[station]={'matched':sum(row['matched'] for row in hits),'tested':len(hits),'samples':hits}
    return {'mesh':model.asset,'stations':output}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('result',type=Path)
    parser.add_argument('--origin',type=float,nargs=2,default=[0,0]);parser.add_argument('--along',type=float,nargs=2,default=[0,1])
    args=parser.parse_args();result=inspect(args.mesh,args.origin,args.along)
    args.result.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for station,row in result['stations'].items():print(station,row['matched'],row['tested'],[(r['feature'],r['hit'] and r['hit']['material']) for r in row['samples'] if not r['matched']])
