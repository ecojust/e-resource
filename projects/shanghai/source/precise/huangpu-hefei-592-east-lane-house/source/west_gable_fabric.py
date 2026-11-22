"""Measured partial gable, sloping verge and the narrow run of adjoining clay roof."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import box,Polygon
from west_gable_shutters import side_openings,finish
from material_names import MATERIAL

M=Path(__file__).resolve().parents[1]/'measurements'
SURVEY=json.loads((M/'gable-roof-and-visible-extent.json').read_bytes())
BASE='Hefei gable | blue grey lime plinth'
STONE='Hefei gable | ash lime plinth seam'
DRAIN='Hefei gable | unlit drain cavity'
TIMBER='Hefei gable | dark worn eaves boards'
SOFFIT='Hefei gable | cream eaves underside'
MORTAR='Hefei gable | pale verge bed'
RIDGE='Hefei gable | weathered curved ridge cap'
TILES=('Hefei roof | faded clay','Hefei roof | muted madder clay','Hefei roof | dark russet clay')
PALETTE={DRAIN:finish((42,40,35),.98),BASE:finish((123,127,122),.94),STONE:finish((145,147,138),.97),
         TIMBER:finish((75,67,57),.86),SOFFIT:finish((181,174,154),.95),
         MORTAR:finish((176,162,144),.91),RIDGE:finish((153,118,98),.87),
         **{m:finish(c,.90) for m,c in zip(TILES,[(155,112,96),(141,97,83),(122,83,72)])}}

def slope(y):
    return min(v['slope']*y+v['intercept_m'] for v in SURVEY['profiles'].values())

def yz_prism(b,points,x0,x1,material,name):
    polygon=Polygon(points) if isinstance(points,list) else points
    b.prism(polygon,x0,x1,lambda y,z,x:(x,y,z),material,name)

def slope_band(b,y0,y1,lo,hi,x0,x1,material,name):
    yz_prism(b,[(y0,slope(y0)+lo),(y1,slope(y1)+lo),
                (y1,slope(y1)+hi),(y0,slope(y0)+hi)],x0,x1,material,name)

def add_gable_wall(b):
    ridge= SURVEY['inferred_ridge_yz_m'][0]
    end=SURVEY['wall_end_y_m']
    area=Polygon([(0,0),(end,0),(end,slope(end)),(ridge,slope(ridge)),(0,slope(0))])
    for row in side_openings():
        area=area.difference(box(row['front_y'],row['bottom'],row['back_y'],row['top']))
    drain=box(1.31,.692,1.62,.744)
    area=area.difference(drain)
    yz_prism(b,area,0.,.252,MATERIAL,'Lane-facing pebbled wall with the three through openings')
    # The plinth partly disappears behind the street gate and a tree. Its
    # upper edge is visible at the foot of the two-storey wall.
    plinth=box(0.,.58,end,1.057).difference(drain)
    yz_prism(b,plinth,-.014,.004,BASE,'Dark grey gable plinth with observed drain opening')
    yz_prism(b,drain,.091,.116,DRAIN,'Recessed dark return behind low horizontal drain')
    for i in range(13):
        y=.34+i*.747
        if y<end:
            yz_prism(b,[(y,.675),(y+.007,.675),(y+.007,1.052),(y,1.052)],-.016,-.013,STONE,
                     f'Plinth upright joint {i+1:02}')

def tile(b,left,right,y0,y1,lod,tint,label):
    base0=slope(y0)+.162;base1=slope(y1)+.162
    samples=6 if lod else 11
    top=[];bottom=[]
    # Constant thickness across the curved face; a lowered lip overlaps the next course.
    for y,z,lip in ((y0,base0,.015),(y1,base1,0.)):
        for t in np.linspace(-1,1,samples):
            x=left+(right-left)*(t+1)/2.
            camber=.052*max(0.,1.-t*t)**1.12
            top.append((x,y,z+lip+camber));bottom.append((x,y,z+lip+camber-.018))
    n=2*samples;quad=[]
    for i in range(samples-1):
        quad.extend([(i,i+1,i+1+samples,i+samples),
                    (i+n,i+samples+n,i+1+samples+n,i+1+n),
                    (i,i+n,i+1+n,i+1),
                    (i+samples,i+1+samples,i+1+samples+n,i+samples+n)])
    quad.extend([(0,samples,samples+n,n),(samples-1,samples-1+n,2*samples-1+n,2*samples-1)])
    if y1<y0:quad=[f[::-1] for f in quad]
    b.add(top+bottom,quad,tint,label)

def add_west_gable(b,lod=False):
    add_gable_wall(b)
    ridge= SURVEY['inferred_ridge_yz_m'][0];edge=SURVEY['wall_end_y_m']
    left,right=SURVEY['roof_strip_x_m']
    for face,eaves in [('Street',-.32),('Lane',edge)]:
        start,finish_y=sorted([eaves,ridge])
        slope_band(b,start,finish_y,-.055,.015,left+.022,.27,SOFFIT,face+' visible lining underneath projecting verge')
        slope_band(b,start,finish_y,.005,.106,left,right,TIMBER,face+' sloping timber roof bed')
        slope_band(b,start,finish_y,.057,.137,left-.024,left+.016,MORTAR,face+' narrow pale bed below the clay verge')
        count=max(1,round(abs(eaves-ridge)/.265))
        for j in range(count):
            y0=eaves+(ridge-eaves)*j/count
            y1=eaves+(ridge-eaves)*min(1.,(j+1.12)/count)
            a,c=sorted([y0,y1])
            slope_band(b,a,c,.076,.163,left-.040,left-.024,TILES[(3*j+j//4)%3],face+f' verge clay slip {j+1:02}')
            for i in range(8):
                tile(b,left+(right-left)*i/8,left+(right-left)*(i+.992)/8,y0,y1,lod,
                     TILES[(i*7+j*11+i*j)%3],face+f' lapped clay tile {j+1:02}-{i+1:02}')
    z=slope(ridge)+.165
    # A short curved cap follows the inferred meeting of the visible slopes.
    theta=np.linspace(np.pi,0.,9 if lod else 17)
    section=[(ridge+.116*np.cos(t),z+.101*np.sin(t)) for t in theta]
    section +=[(ridge+.111*np.cos(t),z+.075*np.sin(t)-.006) for t in theta[::-1]]
    for n in range(4):
        x=left+(right-left)*n/4
        yz_prism(b,section,x,left+(right-left)*(n+1)/4-.004,RIDGE,f'Curved ridge cap {n+1:02}')
