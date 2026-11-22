"""Compare first contacts on the two actual openings, contrasting quoins and both window hoods."""
from pathlib import Path
import os,runpy
from gable import *
root=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(root/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def ray(label,start,direction,depth,mat,tol=.006):
        hit=reader.ray(start,direction,4)
        rows.append(dict(part=label,origin=start,direction=direction,expected_m=round(float(depth),6),material=mat,hit=hit,passed=bool(hit and hit['material']==mat and abs(hit['distance_m']-depth)<tol)))
    def front(label,x,z,y,mat):
        ray(label,[float(x),-1.,float(z)],[0,1,0],1+y,mat)
    for i in range(11):
        z=.24+i*COURSE+.124
        front('Pale quoin at the front',LEFT+.20,z,-.053,STONE)
        front('Alternating right end of corner stone',LEFT+.57,z,-.053 if i%2==0 else 0,STONE if i%2==0 else BRICK)
        ray('Left return of corner block',[LEFT-.82,.39,z],[1,0,0],.774,STONE)
    for xc in CENTERS:
        for sign in (-1,1):
            for z in (.62,1.28,1.96,2.58):
                front('Pale jamb',xc+sign*(HALF+.049),z,-.057,CAP)
                front('Dark external upright',xc+sign*(HALF+.014),z,-.156,METAL)
            front('Front rail crosses the jamb',xc+sign*(HALF+.049),1.91,-.149,METAL)
        for dx in (-.34,0,.34):
            front('Front rail covers glazing on this line',xc+dx,2.12,-.149,METAL)
        for dx in (-.40,-.2,0,.2,.4):
            front('Curved projecting hood',xc+dx,arch(dx*HALF/(HALF+.10))+.104,-.106,CAP)
        for z in np.linspace(.73,2.51,10):
            front('Fine metal horizontal in front',xc+.08,z,-.149,METAL)
        for dx in (-.34,0,.34):
            for z in (.81,1.37,2.16,2.58):front('Glass set back behind horizontal rails',xc+dx,z,.175,GLASS)
        for dx in (-.161,.161):front('Two narrow dark sash stiles',xc+dx,1.35,.110,FRAME)
        for z in (1.45,2.26):front('Sash crossing behind rails',xc+.28,z,.106,FRAME)
        front('Stone sill below the two windows',xc+.155,SILL_Z-.052,-.125,SILL)
    for x in (-1.9,-.72,.23,1.42,2.00):
        for z,p in ((.07,.132),(.17,.087),(3.43,.071),(3.50,.110),(3.57,.145)):
            front('Continuous horizontal trim',x,z,-p,SILL)
    return dict(samples=rows,passed=all(r['passed']for r in rows))
