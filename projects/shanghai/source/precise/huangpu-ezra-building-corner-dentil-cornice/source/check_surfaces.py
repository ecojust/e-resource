"""Sample both sash levels, mouldings, the festoon, and teeth on three different facade planes."""
from pathlib import Path
import os,runpy
from gable import *
project=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',Path(__file__).resolve().parents[4]))
Reader=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']
def check(reader):
    rows=[]
    def shoot(name,x,z,y,mat,side=0):
        t=side*30*pi/180;axis=side*1.46;xx=axis+(x-axis)*cos(t)-y*sin(t);yy=(x-axis)*sin(t)+y*cos(t);direction=[-sin(t),cos(t),0]
        origin=[float(xx-direction[0]*1.6),float(yy-direction[1]*1.6),float(z)];h=reader.ray(origin,direction,3)
        rows.append(dict(part=name,origin=origin,direction=direction,material=mat,hit=h,passed=bool(h and h['material']==mat and abs(h['distance_m']-1.6)<.005)))
    for lo,hi,ra in LEVELS:
        for side in [-1,1]:
            x=side*(ra+.071)
            for z in [lo+.23,(hi+lo)/2,hi-.13]:shoot('Window stone reveal',x,z,-.115,STONE)
            for z in [lo+.24,(hi+lo)/2,hi-.10]:shoot('Recessed sash glass',side*.31,z,.271,GLASS)
        for x in [-.43,0.,.43]:shoot('Square head',x,hi+.06,-.115,STONE);shoot('Projecting sill',x,lo-.055,-.188,STONE)
        for z in [lo+.2,(lo+hi)/2]:shoot('Central timber stile',0,z,.18,SASH)
    for z in [2.65,2.79,2.86]:shoot('Central lower window tab',0,z,-.19,STONE)
    for x in [-.67,-.28,.28,.67]:shoot('Lower cap edge',x,3.03,-.284,CORNICE)
    for x in np.linspace(-.83,.83,10):
        z=6.82+.30*(x/.84)**2;shoot('Raised flower centre',x,z,-.202,STONE)
    for side,lo,hi in [(0,-1.46,1.46),(-1,-2.82,-1.46),(1,1.46,2.82)]:
        n=max(1,round((hi-lo)/.26))
        for j in range(1,n-1):
            x=lo+(j+.5)*(hi-lo)/n;shoot('Dentil face',x,5.80,-.418,CORNICE,side)
            shoot('Dark slot between dentils',x+(hi-lo)/n*.5,5.80,-.124,COVE,side)
        mid=(lo+hi)/2;shoot('Projecting top edge',mid,6.083,-.595,CORNICE,side);shoot('Lower bead',mid,5.128,-.084,STONE,side)
    return dict(passed=all(row['passed'] for row in rows),samples=rows)
