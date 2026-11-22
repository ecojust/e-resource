"""First visible surfaces of the courtyard and tiled entrance in the exported meshes."""
from pathlib import Path
import json
import runpy
import sys
import numpy as np
from shapely.geometry import Point,Polygon

HERE=Path(__file__).resolve().parent
SRC=HERE.parents[2]/'source/precise/huangpu-zhengjia-lane-39-street-gate/source'
sys.path.insert(0,str(SRC))
from courtyard_placement import to_entrance
from courtyard_fabric import MATERIAL,PLINTH,BOARD,EAVE,UNIT,CLIPS,GREEN,YELLOW,TERRAS,COURT
from courtyard_photo_plane import on_end,EYE
from entrance_ground import TILE,FLANK_TILE,ACC,CURB,BLOCKS
from zheng_gate_camera import matrix,plane
inspect=runpy.run_path(HERE.parent/'central-reserve-bank-changshu-front-v1/verify-export.py')['inspect']

def probes():
    cases=[]
    def sight(label,source,target,materials,tolerance=.12):
        source,target=np.array(source),np.array(target)
        distance=float(np.linalg.norm(target-source))
        cases.append(dict(name=label,origin=source.tolist(),direction=((target-source)/distance).tolist(),length=distance+tolerance+.005,allowed=materials,range_m=[distance-tolerance,distance+tolerance]))
    def house(label,u,v,plane_y,material,tolerance=.12):
        sight(label,to_entrance(EYE),to_entrance(on_end(u,v,plane_y)),material,tolerance)
    for n,(u,v) in enumerate([[480,2060],[1012,2025],[1502,2160],[1826,2120],[2220,2222],[890,2505],[1270,2558],[1584,2535],[2121,2597],[915,2840],[1520,3050],[858,3548],[1534,3560],[2290,3505],[1336,3743]]):
        if (u,v)==(1534,3560):
            # This retained original-photo witness falls on the barred ground-floor window.
            house('Right edge of ground-floor security grille',u,v,.069,['Zhengjia | painted glazing bars'],.018)
        else:
            house(f'Sand-finished courtyard wall {n+1}',u,v,0,[MATERIAL])
    for n,(u,v) in enumerate([[960,3868],[1230,3819],[1490,3821],[1650,3795],[1975,3788],[2150,3804]]):
        house(f'Main rendered plinth {n+1}',u,v,-.015,[PLINTH])
    for n,(u,v) in enumerate([[1133,1725],[1375,1754],[1572,1784],[1800,1805]]):
        house(f'Tile face on main roof {n+1}',u,v,.75,TERRAS,2.2)
    for n,(u,v) in enumerate([[836,1815],[1290,1838],[1610,1854],[1812,1865],[2050,1873]]):
        house(f'Dark timber fascia {n+1}',u,v,-.326,[EAVE],.09)
    for n,(u,v)in enumerate([[720,2425],[2040,2470],[1852,2877],[762,3322]]):
        house(f'Stamped metal cabinet {n+1}',u,v,-.249,[UNIT])
    record=json.loads((SRC.parent/'measurements/housekeeping-paint.json').read_bytes())
    for n,(u,v) in enumerate(record['fasteners']):
        house(f'Sign mounting clip {n+1}',u,v,-.076,[CLIPS],.014)
    for row in record['pigment']:
        outline=Polygon(row['shell'],row['holes'])
        xmin,ymin,xmax,ymax=outline.bounds
        interior=[]
        for v in range(int(ymin)+2,int(ymax),2):
            for u in range(int(xmin)+2,int(xmax),2):
                p=Point(u,v)
                if outline.contains(p) and outline.boundary.distance(p)>2.7:interior.append((u,v))
        for n,j in enumerate(np.linspace(0,len(interior)-1,9,dtype=int)):
            house(f"Paint on {row['mark']} section {n+1}",*interior[j],-.070,[YELLOW],.01)
    for n,(u,v) in enumerate([[900,3271],[1105,3271],[895,3390],[1097,3394],[1000,3291]]):
        house(f'Green sign field {n+1}',u,v,-.066,[GREEN],.012)
    def street(label,uv,axis,offset,mats,tol):
        c=matrix('center15');eye=-np.linalg.solve(c[:,:3],c[:,3]);target=plane(uv,axis,offset,'center15')
        sight(label,eye,target,mats,tol)
    for i,(u,y0,y1)in enumerate([(307,435.5,460.),(313,435.,462.),(319,435.,462.),(323,435.,463.),(334,435.,463.),(344,435.,463.),(357,435.,463.),(370,434.,462.),(382,433.,461.),(395,430.,459.)]):
        for j,t in enumerate((.23,.57,.88)):
            street(f'Curved planter, tile sample {i+1}, bed {j+1}',[u,y0+(y1-y0)*t],2,.5661*(1-t),TILE,.31)
    f=json.loads((SRC.parent/'measurements/flanking-tiled-wall.json').read_bytes())
    y=f['surface_plane_y_m']
    for r,v in enumerate([354,358,362,366,369,373,377,380,384,387,391,394,398,402,405,409,412,416]):
        for k,u in enumerate([626,632]):
            street(f'Right-hand tile wall, course {r+1}, panel {k+1}',[u,v],1,y,FLANK_TILE,.023)
    for i,(x,y)in enumerate([(0,.35),(-1.,1.3),(.5,2.57),(-.90,3.75),(1.05,4.10)]):
        sight(f'Grey access paving {i+1}',[x,y,1.],[x,y,-.005],[ACC],.013)
    for i,(x,y)in enumerate([(-3.,-2.13),(0.,-1.75),(2.01,-2.82),(3.8,-2.38)]):
        sight(f'Concrete by the transverse house {i+1}',to_entrance([x,y,.88]),to_entrance([x,y,-.03]),[COURT],.018)
    return cases

if __name__=='__main__':
    rows={name:inspect(Path(path),probes())for name,path in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    for role,row in rows.items():print(role,len(row['cases']),[(c['name'],(c['first_hit']or{}).get('material')) for c in row['cases']if not c['passed']])
    sys.exit(int(any(not r['passed']for r in rows.values())))
