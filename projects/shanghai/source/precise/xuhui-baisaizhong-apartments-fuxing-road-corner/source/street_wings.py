"""Two separately measured street wings and the lower openings on the historical ground plan."""
import numpy as np
from shapely.geometry import box
from materials import STUCCO,PALE,BASE,BAND,FRAME,GLASS,DARK
from plan import STREETS,LEVELS,wall
import corbel_bay

WINGS={
 'fuxing':{'width':3.06,'centre':2.87,'street_bays':[(1.19,3.86),(4.81,7.56)],'col_at':[2.40,6.10],'outer_centre':6.29,'outer_window_width':1.58},
 'wulumuqi':{'width':3.10,'centre':2.83,'street_bays':[(1.15,3.51),(4.25,6.62)],'col_at':[2.28,5.41],'outer_centre':5.64,'outer_window_width':1.54}}
def basis(street):
    a,c=STREETS[street];axis=(c-a)/np.linalg.norm(c-a)
    n=np.array([axis[1],-axis[0]])*(1 if street=='wulumuqi' else -1)
    return a,c,axis,n

def local_bay(b,street,data,lod):
    a,c,d,n=basis(street)
    k=len(b.parts)
    layout=dict(label='Fuxing window' if street=='fuxing' else 'Wulumuqi window',width=data['width'],projection=.82,
                floor_z=[*LEVELS[2:-1],16.40],lower_window=True,upper_lights=3,lower_lights=3)
    corbel_bay.add_corbel_bay(b,layout,lod)
    # Retain both handed coordinate systems' outward normals after placement.
    x=d if street=='wulumuqi'else -d
    matrix=np.array([[x[0],-n[0],0],[x[1],-n[1],0],[0,0,1]])
    origin=np.r_[a+d*data['centre'],0]
    for row in b.parts[k:]:row['vertices']=(np.asarray(row['vertices'])@matrix.T+origin).tolist()
    return layout

def add_wing(b,street,lod):
    data=WINGS[street];a,c,axis,out=basis(street);length=np.linalg.norm(c-a)
    def panel(shape,inside,outer,material,name):
        wall(b,a,c,shape,inside,outer,material,street+' '+name,out)
    layout=local_bay(b,street,data,lod)
    surface=box(0,0,length,16.40)
    centre=data['centre'];width=data['width']
    surface=surface.difference(box(centre-width/2+.13,LEVELS[2]-.02,centre+width/2-.13,16.39))
    low=corbel_bay.openings(layout)[0]
    surface=surface.difference(box(centre+low['x0'],low['z0'],centre+low['x1'],low['z1']))
    # On the 1930s plan, each wide ground aperture has an intermediate square
    # post. Its position along the two streets differs from wing to wing.
    for i,((u,v),post) in enumerate(zip(data['street_bays'],data['col_at'])):
        z0,z1=.19,LEVELS[1]-.21
        surface=surface.difference(box(u,z0,v,z1))
        gate=box(u+.09,0,post-.10,z1-.31)
        # A pedestrian shop door has replaced the vehicle leaves seen in the
        # Forman plate. Keep its deeper glass and threshold clear of the optional early ironwork.
        glazing=box(u,z0,v,z1).difference(gate)
        panel(glazing,-.31,-.285,GLASS,f'ground recessed shop glazing {i+1}')
        panel(gate,-.38,-.36,GLASS,f'ground recessed shop door {i+1}')
        panel(gate.difference(gate.buffer(-.052,join_style=2)),-.33,-.28,FRAME,'shop door steel frame')
        panel(box(u+.14,.83,u+.18,1.13),-.26,-.202,BASE,'shop door pull')
        panel(box(post+.06,.04,v-.02,.33),-.242,-.19,BASE,'shopfront stone sill')
        for s in [u+.026,post,v-.026]:
            panel(box(s-.026,z0,s+.026,z1),-.22,-.15,FRAME,'ground steel jamb')
        panel(box(post-.078,.02,post+.078,z1+.035),-.11,-.025,PALE,'original square ground post')
        for h in [z0+.018,z1-.035,z1-.35]:
            panel(box(u,h-.018,v,h+.018),-.20,-.145,FRAME,'ground glazing rail')
    # The outer stack is separate from the broad projecting window and its
    # consoles. Both dated street views show four real windows in this position.
    sec=data['outer_centre'];wid=data['outer_window_width']
    for floor,(base,top) in enumerate(zip(LEVELS[1:-1],LEVELS[2:]),start=2):
        lo=base+(.64 if floor==2 else .94);hi=top-(.57 if floor==2 else .66)
        x0,x1=sec-wid/2,sec+wid/2
        opening=box(x0,lo,x1,hi)
        surface=surface.difference(opening)
        panel(opening,-.178,-.158,GLASS,f'outside window {floor} glazing')
        panel(opening.difference(opening.buffer(-.054,join_style=2)),-.148,-.092,FRAME,'outer steel sash frame')
        bars=3 if street=='fuxing' else 2
        for j in range(1,bars):
            pos=x0+wid*j/bars
            panel(box(pos-.020,lo+.045,pos+.020,hi-.045),-.14,-.097,FRAME,'outer sash mullion')
        mid=lo+.42*(hi-lo)
        panel(box(x0+.04,mid-.020,x1-.04,mid+.020),-.139,-.095,FRAME,'outer sash meeting rail')
        panel(box(x0-.045,hi+.018,x1+.045,hi+.134),.011,.102,PALE,'outer window projecting head')
        panel(box(x0-.04,lo-.12,x1+.04,lo-.012),.006,.094,BAND,'outer window stone sill')
    panel(surface,-.21,0,STUCCO,'ivory wall with through openings')
    panel(surface.intersection(box(0,0,length,.28)),-.014,.034,BASE,'continuous low stone plinth')
    # Slender ribs frame that second stack in both the 2015 and 2020 surveys.
    for x in [sec-wid/2-.20,sec+wid/2+.15]:
        panel(box(x,LEVELS[1]+.19,x+.045,16.23),.005,.046,BAND,'outer stack narrow vertical rib')
    for z in LEVELS[2:-1]:
        panel(box(sec-.29,z-.24,sec+.29,z+.20),.003,.026,PALE,'outer bay spandrel inset')

def add_wings(b,lod=False):
    for street in STREETS:add_wing(b,street,lod)
