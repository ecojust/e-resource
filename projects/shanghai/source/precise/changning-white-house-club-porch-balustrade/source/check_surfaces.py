"""Inspect the actual decoded faces of the porch, each baluster and the apertures."""
from pathlib import Path
import os,runpy
from gable import *
p=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def test(part,x,z,depth,material,tol=.012):
        origin=[x,-2.,z];hit=reader.ray(origin,[0,1,0],6)
        ok=hit is None if depth is None else bool(hit and hit['material']==material and abs(hit['distance_m']-(2+depth))<tol)
        rows.append(dict(part=part,origin=origin,hit=hit,material=material,depth=depth,passed=ok))
    for x in BALUSTERS:
        for z,rad in [(3.512,.073),(3.627,.044),(3.801,.077),(3.94,.050)]:test('Turned front baluster',x,z,-.444-rad,STONE)
    for a,c in zip(BALUSTERS,BALUSTERS[1:]):
        test('Open grille gap',(a+c)/2,3.84,None,None)
    for x in [-1.66,-.81,-.30,.21,.75,1.63]:
        for z,y,mat in [(3.302,-.565,STONE),(3.387,-.61,RECESS),(3.425,-.665,STONE),(4.092,-.55,STONE),(4.161,-.575,RECESS)]:test('Layered horizontal stone',x,z,y,mat)
    for side in (-1,1):
        x=side*AX
        for z,rad in [(.15,.214),(.30,.176),(1.53,.157),(2.44,.148),(2.75,.178)]:test('Tapered column and mouldings',x,z,FRONT-rad,SHAFT)
        test('Capital below relief',x,2.882,FRONT-.225,STONE)
        test('Raised central relief',x,3.049,FRONT-.409/2-.039,FACE)
        test('Paired eye on relief',x+.042,3.085,FRONT-.409/2-.032,SHADOW)
        for z in [.42,1.23,1.91]:test('Jamb on the recessed arch',side*.89,z,.545,STONE)
    for j in range(9):
        a=(j+.5)*pi/9;test('Actual voussoir',.93*cos(a),2.28+.745*sin(a),.48 if j==4 else .525,STONE)
    test('Timber lock stile',-.634,1.05,.710,WOOD)
    test('Timber bottom rail',.41,.11,.710,WOOD)
    test('Transom below the fan',-.31,2.246,.675,WOOD)
    for x,z in [(.163,.643),(-.05,1.67),(.30,1.41),(-.33,.55)]:test('Diamond pane',x,z,.778,GLASS)
    test('Diagonal metal at the lower left glazing strip',-.40,.55,.738,METAL)
    for sign in (-1,1):
        for z in (.49,1.15,1.49):
            x=sign*(z-1.10)*.45;test('Diagonal metal door bar',x,z,.737,METAL)
    for j in range(1,6):
        a=j*pi/6;r=.23;test('Fanlight spoke',r*cos(a),2.28+.795*r*sin(a),.710,METAL)
    for j in range(1,6):
        a=(j+.37)*pi/6;r=.29;test('Dark glass between real spokes',r*cos(a),2.28+.795*r*sin(a),.772,GLASS)

    return dict(passed=all(r['passed'] for r in rows),samples=rows)
