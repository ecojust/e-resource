"""Close the northwest roof row to its surveyed footprint and the photograph's street gables."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from street314 import RED, CAP, PIPE

HERE=Path(__file__).resolve().parent
TILE='Yiqingli | weathered clay tile'
PEAK='Yiqingli | worn clay ridge'
PALETTE={TILE:{'texture':str(HERE/'yiqingli-roof-tile.png'),'color':[1.,1.,1.],'roughness':.94},
         PEAK:{'color':[.188,.094,.06],'roughness':.92}}

def tile_quad(b,points,material,label):
    """Create a closed roof panel in either planar or slightly skewed plan coordinates."""
    top=np.asarray(points,dtype=float)
    cross=np.cross(top[1]-top[0],top[2]-top[0])
    if cross[2]<0:top=top[::-1]
    floor=top-[0,0,.092]
    vertices=np.vstack((top,floor))
    faces=[(0,1,2),(0,2,3),(6,5,4),(7,6,4)]
    for i in range(4):
        n=(i+1)%4;faces.append((i,i+4,n+4,n))
    b.add(vertices,faces,material,label)

def wall_segment(b,a,z,lower,upper,material,label):
    a=np.asarray(a,float);z=np.asarray(z,float)
    t=z-a;L=np.linalg.norm(t);t/=L
    # Boundary is traversed anticlockwise. Positive depth is exterior.
    n=np.array([t[1],-t[0]])
    shape=Polygon([(0,lower),(L,lower),(L,upper[1]),(0,upper[0])])
    b.prism(shape,-.235,0,lambda u,h,d:(*(a+t*u+n*d),h),material,label)

def point_on_line(housing,s,t,elevation):
    left=np.asarray(housing['front_left'])+(np.asarray(housing['back_left'])-housing['front_left'])*t
    right=np.asarray(housing['front_right'])+(np.asarray(housing['back_right'])-housing['front_right'])*t
    if t < housing.get('straight_return',0.):
        left[0]=housing['front_left'][0]
    elif 'straight_return' in housing:
        v=(t-housing['straight_return'])/(1-housing['straight_return'])
        left[0]=housing['front_left'][0]+(housing['back_left'][0]-housing['front_left'][0])*v
    x,y=left+(right-left)*s
    return [x,y,elevation]

def add_314_roof(b,lod):
    reg=json.loads((HERE/'roof-survey.json').read_bytes())['row_314']
    across=reg['across'];sections=reg['sections']
    grids=[]
    for section in sections:
        t=section['t']
        fractions=list(across)
        fractions[2]+=(reg['back_ridge_fraction']-fractions[2])*t
        profile=[point_on_line(reg,s,t,z) for s,z in zip(fractions,section['heights'])]
        if t <= reg['straight_return']:
            profile[0][0]+=.09
        if t == 0.:
            for point in profile:point[1]+=.09
        grids.append(profile)
    for j,(near,far) in enumerate(zip(grids,grids[1:])):
        for i in range(len(across)-1):
            tile_quad(b,[near[i],near[i+1],far[i+1],far[i]],TILE,f'314 clay roof section {j+1}-{i+1}')
    ridge=[row[2] for row in grids]
    b.tube(ridge,.071,PEAK,8 if lod else 14,'314 main longitudinal ridge')
    # The roof projecting into the close gable terminates below its plaster top.
    b.tube([grids[1][0],grids[1][1]],.056,PEAK,8 if lod else 12,'314 northwest transverse ridge')
    for j in range(len(sections)-1):
        a0,a1=grids[j][-1],grids[j+1][-1]
        wall_segment(b,a0[:2],a1[:2],0,[a0[2]-.092,a1[2]-.092],RED,'314 southeast flank')
        b.tube([[*a0[:2],a0[2]-.03],[*a1[:2],a1[2]-.03]],.048,CAP,7 if lod else 12,'314 southeast drip')
        if sections[j]['t']+1e-6<reg['straight_return']:continue
        p=grids[j+1][0];q=grids[j][0]
        wall_segment(b,p[:2],q[:2],0,[p[2]-.092,q[2]-.092],RED,'314 back part of northwest flank')
    rear=grids[-1]
    for i in reversed(range(len(rear)-1)):
        p=rear[i+1];q=rear[i]
        wall_segment(b,p[:2],q[:2],0,[p[2]-.092,q[2]-.092],RED,'314 rear roof outline')
    # An original roof, with a visible underside at the eaves. Interior floor
    # plans are not inferred from the government's group address.
    base=Polygon([reg['front_left'],reg['front_right'],reg['back_right'],reg['back_left']]).buffer(-.12,join_style=2)
    b.plan_prism(base,-.11,.012,CAP,'314 housing floor')
