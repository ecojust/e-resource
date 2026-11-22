"""Test material and signed depth of the stone, sash, bars and glazing on the actual decoded meshes."""
import os,runpy
from math import sin,cos,pi
from pathlib import Path
from gable import STONE,MORTAR,SILL,SASH,GRILLE,GLASS,VENT,HALF,RISE,SPRING
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def hit(label,x,z,mat,depth):
        pos=[x,-1.,z];direction=[0,1,0];h=reader.ray(pos,direction,3)
        rows.append(dict(part=label,origin=pos,direction=direction,expected_material=mat,expected_distance=1+depth,
                         hit=h,passed=bool(h and h['material']==mat and abs(h['distance_m']-1-depth)<.011)))
    for i in range(11):
        angle=(i+.5)*pi/11
        hit('Carved stone voussoir',(HALF+.145)*cos(angle),SPRING+(RISE+.145)*sin(angle),STONE,-.017)
    for i in range(1,10):
        angle=i*pi/11
        hit('Open radial mortar joint',(HALF+.14)*cos(angle),SPRING+(RISE+.14)*sin(angle),MORTAR,.046)
        for x in (-1.32,1.32):
            z=.84+(3.22-.84)*i/10
            hit('Joint in the stone pier',x,z,MORTAR,.046)
            hit('Face of individual stone',x,z+.055,STONE,-.016)
    for x in (-.79,-.39,.39,.79):
        hit('Glazing behind both ranks of metal',x,2.05,GLASS,.271)
        hit('Actual wall of sill section',x,.84,SILL,-.132)
        hit('Dark sash transom',x,2.27,SASH,.145)
    for x in (-.65,-.25,.25,.65):
        hit('Horizontal tie of the grille',x,2.96,GRILLE,-.059)
    left=reader.ray([-.37,-1.,2.05],[0,1,0],3)
    right=reader.ray([.37,-1.,2.05],[0,1,0],3)
    # Haute and lower detail distribute rod centres differently. Both actual intersections are retained.
    for x,value in [(-.37,left),(.37,right)]:
        material=value['material'] if value else None
        ok=bool(value and ((material==GRILLE and abs(value['distance_m']-.933)<.006) or (material==GLASS and abs(value['distance_m']-1.271)<.006)))
        rows.append(dict(part='High-detail upright or lower-detail gap at the photographed test line',origin=[x,-1.,2.05],direction=[0,1,0],hit=value,passed=ok))
    for z in (1.22,2.08,2.80,3.57,3.98):
        hit('Fine continuous centre upright',0,z,GRILLE,-.067)
    for x in [-.48,-.21,0,.21,.48]:
        hit('Blind slot in the apron',x,.251,VENT,.039)
        hit('Plain panel above slot',x,.55,STONE,0)
    return dict(passed=all(r['passed']for r in rows),samples=rows)
