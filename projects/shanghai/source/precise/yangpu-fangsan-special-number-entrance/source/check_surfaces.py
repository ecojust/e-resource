"""Cast rays into the decoded geometry at architectural features visible in the two photographs."""
from pathlib import Path
import os,runpy,json
from shapely.geometry import Polygon
from entrance import *
base=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(base/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']

def check(reader):
    rows=[]
    def ray(label,origin,direction,material,expected,tolerance=.021):
        hit=reader.ray(origin,direction,5)
        ok=bool(hit and hit['material']==material and abs(hit['distance_m']-expected)<=tolerance)
        rows.append(dict(part=label,origin=origin,direction=direction,expected=material,expected_m=expected,tolerance_m=tolerance,hit=hit,passed=ok))
    for index in range(7):
        y=-2.88+index*.297
        top=(index+1)*.153
        for x in [-1.05,-.44,.68,1.16]:
            ray('Horizontal tread '+str(index+1),[x,y+.12,1.53],[0,0,-1],STONE,1.53-top)
            ray('Vertical stone face '+str(index+1),[x,y-.10,top-.074],[0,1,0],RISER,.1)
    for side in [-1,1]:
        x=side*1.247
        for z in [1.28,1.66,2.18,2.77,3.24]:
            ray('Solid face between column flutes',[x+.051,-1.21,z],[0,1,0],CREAM,.43)
        for z in [1.66,2.18,2.77]:
            ray('Recessed shaft fluting',[x,-1.21,z],[0,1,0],CREAM,.448,.014)
        ray('Foot of square shaft',[x,-1.21,1.107],[0,1,0],SHADE,.4025)
        ray('Side beam seen from below',[x,.06,3.47],[0,0,1],SHADE,.2065)
        for i in (0,3,6):
            y=-2.88+(i+.52)*.297
            ray('Tubular rail post',[side*1.48-.09,y,(i+1)*.153+.20],[1,0,0],RED,.066,.015)
    for x in [-.28,-.15,.18,.28]:
        ray('Brown recessed door head',[x,-.05,3.375],[0,1,0],TIMBER,.894)
        ray('Dark recessed panel',[x,-.05,1.49],[0,1,0],DARK,1.020)
    for x in [-.39,-.13,.12,.39]:
        for z in [4.68,4.95,5.33]:
            ray('Stair window pane',[x,.4,z],[0,1,0],GLASS,.469)
    for x in [-.252,0,.252]:
        ray('Stair window steel stile',[x,.4,4.99],[0,1,0],STEEL,.4)
    for z in [4.829,5.165]:
        ray('Stair window steel crossbar',[.108,.4,z],[0,1,0],STEEL,.4)
    ray('Roof face beyond the projected brackets',[0,-1.62,4.027],[0,1,0],CREAM,.470)
    ray('Enamel plate field',[-.915,.40,3.328],[0,1,0],GREEN,.341)
    for line in json.loads(Path(__file__).with_name('plate-letters.json').read_bytes()):
        mat=YELLOW if line['text']=='特号' else WHITE
        polys=[Polygon(r[0],r[1:])for r in line['polygons']]
        for p in sorted(polys,key=lambda o:o.area,reverse=True)[:5]:
            pt=p.buffer(-.0001).representative_point()
            ray('Address lettering '+line['text'],[pt.x,.4,pt.y],[0,1,0],mat,.337,.004)
    return dict(passed=all(r['passed']for r in rows),samples=rows)
