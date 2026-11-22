"""Test the material at tile ends, individual brackets, troughs and the ridge."""
from pathlib import Path
import runpy,os
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def record(name,pt,vec,mat,expected,tol):
        hit=reader.ray(pt,vec,6)
        rows.append(dict(part=name,origin=pt,direction=vec,expected_m=expected,material=mat,hit=hit,passed=bool(hit and hit['material']==mat and abs(hit['distance_m']-expected)<tol)))
    for u in ROLLS:
        x,y,z=point('front',u,0);record('Round drip edge',[x,-2.25,z+.012],[0,1,0],CAP,2.25+Y0-.025,.003)
    for x in BRACKETS:
        for z,y,mat in [(.25,-.31,DARK),(.40,-.46,WOOD),(.365,-.39,WOOD),(.52,-.46,WOOD),(.64,-.67,WOOD),(.746,-.61,WOOD),(.958,-.71,WOOD)]:
            record('Stepped bracket arm',[x,-2.25,z],[0,1,0],mat,2.25+y,.003)
    for x in [-2.11,-1.05,0,1.05,2.11]:
        record('Shadow between bracket groups',[x,-2.25,.28],[0,1,0],FASCIA,2.25-.036,.003)
        record('Long head beam',[x,-2.25,1.078],[0,1,0],DARK,2.25-.76,.003)
        record('Second fascia',[x,-2.25,1.170],[0,1,0],WOOD,2.25-.89,.003)
    for u1,u2 in zip(ROLLS[3:-4:2],ROLLS[4:-3:2]):
        for s in [.32,.63]:
            x,y,z=point('front',(u1+u2)/2,s)
            record('Concave tile bed',[x,y,4],[0,0,-1],FACE,4-z,.016)
        x,y,z=point('front',u1,.36)
        record('Raised tile roll',[x,y,4],[0,0,-1],TILE,4-z-.084,.025)
    for x in np.linspace(-2.2,2.2,9):record('Raised ridge crest',[x,Y1,4],[0,0,-1],RIM,4-HIGH-.17,.003)
    return dict(samples=rows,passed=all(row['passed']for row in rows))
