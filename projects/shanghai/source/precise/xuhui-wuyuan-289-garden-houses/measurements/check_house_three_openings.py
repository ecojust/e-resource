"""Cast registered rays from the two numbered-house photographs onto an actual GLB."""
from pathlib import Path
import argparse, json, sys
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
sys.path.insert(0,str(HERE.parent/'source'))
from glb_triangles import SerialScene
from placement import Facade
from materials import BRICK, CREAM, SILL, IRON, OAK, DOOR, BOARD, LETTER, GLASS, SASH, STEP, DARK
PLATE=(BOARD,LETTER);GATE=(IRON,DOOR,DARK);PANE=(GLASS,SASH)
# Positions were read on each 710px-high photograph, then scaled to its preserved native raster.
WITNESSES={
'gao-08':[
 ('plate green or numeral',72,409,PLATE),('door lower gridded leaf',85,544,GATE),
 ('door upper gridded leaf',94,437,GATE),('adjacent wall between openings',139,476,(BRICK,)),
 ('far brick on right of door',143,559,(BRICK,)),('upper step',99,616,(STEP,)),
 ('middle stair',98,648,(STEP,)),('first window centre',160,470,PANE),('first window sill',163,523,(SILL,)),
 ('plaster panel under lower diagonal',100,252,(CREAM,)),('plaster left of main sash',117,157,(CREAM,)),
 ('plaster below main sill',146,278,(CREAM,)),('upper left first casement',152,197,PANE),
 ('upper right second casement',179,228,PANE),('attic casement',216,131,PANE),
 ('projecting wing short brick return',227,546,(BRICK,)),('projecting wing side below belt',222,495,(BRICK,)),
 ('garden-facing edge of projecting brick wall',257,554,(BRICK,)),('opened metal casement',274,480,PANE),
 ('front upper side cream panel',234,280,(CREAM,)),('main gable base plate',138,328,(OAK,)),
 ('left main gable post',81,188,(OAK,))],
'museum-current':[
 ('plaque beside door below later awning',304,405,PLATE),('No 3 lower door',327,474,GATE),
 ('No 3 upper door',325,425,GATE),('red wall between openings',347,468,(BRICK,)),('red wall below right opening',365,480,(BRICK,)),
 ('first casement',362,437,PANE),('sill',366,462,(SILL,)),('edge of middle step',335,527,(STEP,)),
 ('upper small-pane casement',328,278,PANE),('second upper casement',346,292,PANE),
 ('main gable plaster panel',308,225,(CREAM,)),('lower plaster panel',317,323,(CREAM,)),
 ('gable cream infill',340,211,(CREAM,)),('main gable belt',334,356,(OAK,)),
 ('projecting wing return face',408,454,(BRICK,)),('projecting wing return face above pipes',401,434,(BRICK,)),
 ('projecting wing upper return panel',398,310,(CREAM,)),('small gable third lower opening',454,438,PANE)]}
def inspect(mesh,local=False):
    source=json.loads((HERE/'house-three-two-registered-views.json').read_bytes())
    scene=SerialScene(mesh);f=Facade(None,'3-4',origin=(0.,0.),along=(1.,0.)) if local else Facade(None,'3-4')
    stations={}
    for row in source['stations']:
        key=row['source']['name'];matrix=np.asarray(row['P']);inverse=np.linalg.inv(matrix[:,:3]);eye=-inverse@matrix[:,3]
        origin=np.asarray(f.point(*eye));tests=[];scale=np.asarray(row['source']['dimensions'])/row['observed_image_size']
        for name,x,y,expected in WITNESSES[key]:
            xyz=eye+inverse@[x,y,1];direction=np.asarray(f.point(*xyz))-origin
            hit=scene.ray(origin,direction,70)
            tests.append({'feature':name,'native_pixel':np.round(np.array([x,y])*scale,2).tolist(),'expected':expected,'first_hit':hit,'matched':bool(hit and hit['material'] in expected)})
        stations[key]={'total':len(tests),'matched':sum(r['matched'] for r in tests),'rays':tests}
    return {'mesh':scene.asset,'coordinate_space':'local facade' if local else 'two-house authored scene','stations':stations}
if __name__=='__main__':
    arg=argparse.ArgumentParser();arg.add_argument('glb',type=Path);arg.add_argument('output',type=Path);arg.add_argument('--local',action='store_true');args=arg.parse_args()
    d=inspect(args.glb,args.local);args.output.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
    for k,v in d['stations'].items():print(k,v['matched'],v['total'],[(r['feature'],r['first_hit'] and r['first_hit']['material']) for r in v['rays'] if not r['matched']])
