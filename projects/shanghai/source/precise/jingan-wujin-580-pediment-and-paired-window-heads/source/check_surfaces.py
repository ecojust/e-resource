"""Verify material, depth and the open shape of the two brick rings in all delivered models."""
from pathlib import Path
import os,runpy
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def probe(name,x,z,y,material,tol=.006):
        h=reader.ray([float(x),-1.,float(z)],[0,1,0],3)
        rows.append(dict(part=name,origin=[float(x),-1.,float(z)],hit=h,material=material,depth_m=y,passed=bool(h and h['material']==material and abs(h['distance_m']-(1+y))<tol)))
    for side in [-1,1]:
        for z in [2.51,2.83,3.11,3.47,3.78]:probe('Pilaster shaft',GX+side*.89,z,-.22,TILE)
        probe('Pilaster cap',GX+side*.89,4.095,-.251,TILE);probe('Pilaster foot',GX+side*.89,2.20,-.238,STONE)
        for z in [2.62,3.01,3.42]:probe('Recessed upper glazing',GX+side*.31,z,.055,GLASS)
        for u in [.20,.52,.79]:
            probe('Sloping red outer verge',GX+side*1.27*(1-u),4.30+(5.11-4.30)*u,-.205,TILE)
            probe('Pale gable cap',GX+side*1.295*(1-u),4.379+(5.201-4.379)*u,-.232,STONE)
            probe('Lower pediment apex strip',GX+side*.96*(1-u),.964+(.696)*u,-.228,STONE)
    for z in [2.55,2.72,3.03,3.35]:probe('Vertical window bar',GX,z,.009,FRAME)
    for x in [GX-.45,GX,GX+.46]:probe('Square upper lintel',x,3.70,-.179,TILE);probe('Upper window sill',x,2.38,-.19,STONE)
    for c in WIN:
        for j in [1,3,5,7,9,11]:
            t=(j+.5)*pi/13;probe('Individual brick in segmental arch',c+(RI+.067)*cos(t),S+(ARCH_RISE+.07)*sin(t),-.056,TILE)
        for dx in [-.31,0,.34]:probe('Solid inner brick panel over the window',c+dx,S+.184,.065,PANEL)
        for x in [c-.36,c+.36]:
            probe('Lower window glass visible below arch',x,.82,.165,GLASS);probe('Window transom',x,.57,.105,FRAME)
        probe('Thin horizontal window top',c+.41,S-.016,-.04,FRAME)
    return dict(passed=all(row['passed']for row in rows),samples=rows)
