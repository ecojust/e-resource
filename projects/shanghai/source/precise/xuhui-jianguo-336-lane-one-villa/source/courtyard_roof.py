"""Garden cornice and roof of No. 1, reconstructed from detail 06 and two aerial dates."""
import json
import math
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Polygon
from photo_architecture import Facade
from bay_carvings import STONE, SCULPT, DEEP
from garden_front import BASE

DATA = Path(__file__).absolute().parents[1] / 'measurements/roof-extent.json'
CLAY = 'Fudefang | red clay roof tiles'
CAPPING = 'Fudefang | weathered clay hip capping'
FLAT = 'Fudefang | pale rear roof'
PALETTE = {CAPPING: dict(color=[.49,.238,.158], roughness=.94),
           FLAT: dict(color=[.54,.525,.478], roughness=.97)}


def front_frieze(b, start, end, z, lod):
    face = Facade(b, start, end, 'Cornice | garden')
    length = face.length
    # Section in photograph 06, from the relief bed up to the broad drip edge.
    for level, height, projection, material, name in [
        (-.171,.226,.076,SCULPT,'scroll bed'),(-.031,.062,.129,STONE,'ovolo'),
        (.017,.047,.193,SCULPT,'dentil bead'),(.096,.105,.382,STONE,'coffered soffit'),
        (.171,.050,.329,SCULPT,'recessed fascia'),(.220,.064,.400,STONE,'weathering course')]:
        face.box(0,z+level,length,height,projection+.012,(projection-.012)/2,material,name)
    count=max(1,round((length-.075)/.263))
    pitch=(length-.056)/count
    for j in range(count):
        u0=-length/2+.028+pitch*j
        # The ogee terminates above a short vertical foot in the field photograph.
        a=np.linspace(0,1,8 if lod else 18)
        u=u0+pitch*(.07+.84*a)
        zz=z-.165+.066*np.sin(np.pi*1.76*(a-.14))
        wave=LineString(np.column_stack((u,zz))).buffer(.016,cap_style=1,join_style=2)
        face.prism(wave,.080,.101,DEEP,'continuous reversed scroll in the frieze')
        mid=u0+pitch*.51
        face.box(mid,z+.027,.081,.073,.203,.170,SCULPT,'projected block under cornice')
        if not lod:
            # A diagonally divided panel on each boxed soffit block, visible from below.
            for sign in (-1,1):
                b.tube([face.point(mid+sign*.049,z+.043,.169),
                        face.point(mid,z+.039,.306)],.0125,DEEP,sides=5,label='Cornice | chevron under modillion')
            face.box(mid,z-.032,.057,.038,.066,.119,DEEP,'divider behind modillion')


def raised_triangle(b, a, c, d, material):
    pts=[np.array(v,float) for v in (a,c,d)]
    if np.cross(pts[1]-pts[0],pts[2]-pts[0])[2] < 0:
        pts[1],pts[2]=pts[2],pts[1]
    underside = [p-[0,0,.12] for p in pts]
    b.add(underside+pts,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],
          material,'Roof | hipped weathering surface')


def add_roof(b, lod=False):
    d=json.loads(DATA.read_bytes())
    front=d['front_wall']
    back_w,back_e=d['upper_roof_back_west_east']
    rear=d['rear_wall_y']
    eave=d['soffit_z']; low=d['rear_soffit_z']
    high_plan=Polygon([*front,back_e,back_w])
    lower_plan=Polygon([back_w,back_e,(6.45,rear),(-6.45,rear)])
    house=high_plan.union(lower_plan)
    b.plan_prism(house,-.145,.012,BASE,'Base | ground slab')
    # The east and rear boundaries are documented in plan. There are no verified
    # window schedules for them. Keep the shell continuous across the roof step.
    for a,c,height,label in [(front[-1],back_e,eave,'east high'),(back_e,(6.45,rear),low,'east low'),
                             ((6.45,rear),(-6.45,rear),low,'north')]:
        f=Facade(b,a,c,'Boundary | '+label)
        f.box(0,height/2,f.length,height,.245,-.120,STONE,'wall')
        f.box(0,.17,f.length,.37,.062,.002,BASE,'plinth')
        f.box(0,height+.065,f.length,.125,.31,.017,SCULPT,'straight eave')
    for i,(a,c) in enumerate(zip(front,front[1:])):
        front_frieze(b,a,c,eave,lod)
    b.plan_prism(high_plan.buffer(.398,join_style=2),eave+.192,eave+.254,STONE,'Roof | mitred upper garden rim')
    b.plan_prism(lower_plan.buffer(.23,join_style=2),low+.125,low+.190,FLAT,'Roof | lower northern surface')
    step=Facade(b,back_e,back_w,'Roof | step between the two volumes')
    step.box(0,(low+eave+.34)/2,step.length,eave-low+.16,.245,-.105,STONE,'rear of hipped roof')
    # The buffered eave has the same vertex count as the visible plan. Recover
    # its points in wall order rather than relying on Shapely ring orientation.
    outline=list(high_plan.buffer(.386,join_style=2).exterior.coords)[:-1]
    def top(p):
        x,y=min(outline,key=lambda v:math.dist(v,p))
        return np.array([x,y,eave+.375])
    garden=[top(p) for p in front]
    nw,ne=top(back_w),top(back_e)
    west,east=map(np.array,d['ridge_west_east_xyz'])
    # Local hips run from the change of wing direction into the ridge. Separate
    # shallow wedges keep the two canted front bays visible in the roofline.
    patches=[(garden[i],garden[i+1],west if i<3 else east) for i in range(7)]
    patches += [(garden[3],east,west),(garden[0],west,nw),(garden[-1],ne,east),
                (nw,west,east),(nw,east,ne)]
    for a,c,p in patches:
        raised_triangle(b,a,c,p,CLAY)
    for a,c in [(garden[0],west),(garden[-1],east),(nw,west),(ne,east),(west,east)]:
        b.tube([a+[0,0,.020],c+[0,0,.020]],.056,CAPPING,sides=6 if lod else 12,label='Roof | hip and ridge capping')
