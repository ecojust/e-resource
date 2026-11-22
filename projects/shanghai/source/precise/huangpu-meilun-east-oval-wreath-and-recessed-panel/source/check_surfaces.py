"""Measure the actual convex oval, leaves, window division, front panel and its flutes."""
from pathlib import Path
import os,runpy
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def ray(label,x,z,material,front,tol=.004):
        origin=[float(x),-1.,float(z)];hit=reader.ray(origin,[0,1,0],3)
        rows.append(dict(part=label,origin=origin,direction=[0,1,0],expected_m=1+front,material=material,hit=hit,passed=bool(hit and hit['material']==material and abs(hit['distance_m']-(1+front))<tol)))
    for x,hw in BAYS:
        for dz in (1.29,1.76,2.17,2.87):
            ray('Left stone window moulding',x-hw+.006,dz,EDGE,-.068)
            ray('Right stone window moulding',x+hw-.007,dz,EDGE,-.068)
        for dx in (-.55,-.11,.33,.56):
            for z in (1.48,2.11,2.63):ray('Inset window glazing',x+dx,z,GLASS,.193)
        for dx in (-.48,-.09,.36):ray('Continuous sash cross rail',x+dx,1.814,FRAME,.091)
        ray('Spandrel centre',x,.61,STONE,-.155)
        for z in (.080,.103):ray('Wall separation below spandrel',x+.14,z,STONE,0.)
        for dx in (-.52,.52):ray('Broad spandrel stone',x+dx,.19,EDGE,-.076)
    for i,(x,hw) in enumerate(BAYS):
        half=.405 if i==0 else .46;n=7 if i==0 else 2
        for dx in np.linspace(half+.08,hw-.18,n):
            for side in (-1,1):ray('Fluted spandrel just outside raised rectangle',x+side*dx,.58,DARK,-.107)
        for side in (-1,1):ray('Central panel moulding',x+side*(half-.045),.72,EDGE,-.142)
    for z in (.5,1.06,1.62,2.05):
        ray('Shallow horizontal pier joint',-.27,z+.006,DARK,-.045)
    for theta in np.linspace(0,2*pi,8,endpoint=False):
        x=.112*cos(theta);dz=.167*sin(theta);factor=(max(0,1-(x/.177)**2-(dz/.264)**2))**.5
        ray('Rounded stone boss',x,CZ+dz,BOSS,-.118-.096*factor,.006)
    ray('Forward apex of oval',0,CZ,BOSS,-.214)
    for theta in (pi/7,pi/3,pi*.68,pi*.88,pi*1.18,pi*1.78):
        ray('Deepest oval window moulding',.192*cos(theta),CZ+.281*sin(theta),CART,-.146)
    for sign in (-1,1):
        for j in (1,3,5,7):
            t=j/8;ray('Lower leaf above projecting corner',sign*(.038+.236*t),CZ-.35+.123*t*t,LEAF,-.118)
    for x in (-2.9,-1.75,-.31,.77,1.65):
        for z,d in ((3.125,-.045),(3.165,-.102),(3.225,-.160)):ray('Long top stone moulding',x,z,EDGE,d)
    return dict(samples=rows,passed=all(s['passed']for s in rows))
