"""Read the exact first surface below independently identified northern photo pixels."""
from pathlib import Path
import sys,argparse,json
import numpy as np
HERE=Path(__file__).resolve().parent;PRECISE=HERE.parents[1]
sys.path[:0]=[str(HERE.parent/'source'),str(PRECISE/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from placement import Facade
from materials import *
from glb_triangles import SerialScene
# Unrectified crop from the preserved original photograph, 300,0 to 4247,3239.
GLAZING=(GLASS,SASH,GLINT)
POINTS=[
 ('large gable left light plaster',413,224,(CREAM,)),('large gable panel below sash',436,332,(CREAM,)),
 ('front left ground brick',416,470,(BRICK,)),('front ground brick between openings',453,466,(BRICK,)),
 ('number 1 enamel plate',447,422,(BOARD,LETTER)),('number 1 dark entrance leaf',428,445,(DOOR,DARK,OAK,IRON)),
 ('lower sash glass',465,440,GLAZING),('upper paired casement',431,272,GLAZING),
 ('dark open stair head',343,259,(DARK,DOOR,OAK)),('cream stair side shelter',342,204,(CREAM,)),
 ('number 2 plate',179,350,(BOARD,LETTER)),('plaster flanking stair casement',240,247,(CREAM,)),
 ('upper stair-side glass',197,237,GLAZING),('plaster below upper stair window',252,281,(CREAM,)),
 ('upper stepped brick cheek',319,362,(BRICK,SILL)),('lowest side cheek',208,431,(BRICK,SILL)),
 ('stepped cheek at high landing',356,323,(BRICK,SILL)),('main tall chimney shaft',272,76,(BRICK,SILL)),
 ('limed chimney haunch',281,139,(CREAM,)),('larger gable tile slope',380,140,(TILE,BARGE)),
 ('projecting gable tile slope',496,242,(TILE,BARGE)),('red projecting bay lower panel',524,449,(BRICK,)),
 ('small upper plaster panel',540,314,(CREAM,)),('brick cheek at inner turn',300,398,(BRICK,SILL))]
def inspect(mesh):
    scene=SerialScene(mesh);f=Facade(None,'1-2')
    record=json.loads((HERE/'north-numbered-camera.json').read_bytes());P=np.array(record['native_P']);inv=np.linalg.inv(P[:,:3]);eye=-inv@P[:,3]
    origin=np.array(f.point(*eye));tests=[]
    for label,x,y,materials in POINTS:
        pixel=[300+x*3947/645,y*3239/530]
        ray=inv@[*pixel,1];direction=np.array(f.point(*(eye+ray)))-origin
        hit=scene.ray(origin,direction,70)
        tests.append({'detail':label,'native_pixel':pixel,'expected':materials,'first_hit':hit,'matched':bool(hit and hit['material'] in materials)})
    return {'mesh':scene.asset,'source':'Gao Can 88, 2013, plate 01','native_size':[4247,3239],'tested':len(tests),'matched':sum(t['matched']for t in tests),'rays':tests}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('model',type=Path);parser.add_argument('output',type=Path);v=parser.parse_args()
    r=inspect(v.model);v.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    print(r['matched'],r['tested'],[(t['detail'],t['first_hit'] and t['first_hit']['material'])for t in r['rays']if not t['matched']])
