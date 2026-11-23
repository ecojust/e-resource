"""Paired glass entrance doors beneath the courtyard arch at 325 Changle Road.

Pixel positions refer to Fayhoo's 2037 by 1358 image from 4 April 2015.
The plane of the glass is behind the arch; no interior fittings are reconstructed.
"""
import math
import numpy as np


METAL = '325 garden | brushed door fittings'
DARK = '325 garden | dark door sections'
GRIP = '325 garden | wrapped pull handles'
GLASS = '325 garden | smoked entrance glass'
INTERIOR = '325 garden | shadow behind the entrance'
THRESHOLD = '325 garden | pale entrance threshold'
CHEEK = '325 garden | shaded ochre porch reveal'
PALETTE = {
    METAL: {'color': [.63, .59, .49], 'metallic': .78, 'roughness': .30},
    DARK: {'color': [.041, .043, .038], 'metallic': .51, 'roughness': .45},
    GRIP: {'color': [.036, .036, .031], 'roughness': .68},
    GLASS: {'color': [.037, .037, .028], 'alpha': .55, 'metallic': .09, 'roughness': .22},
    INTERIOR: {'color': [.018, .019, .014], 'roughness': .97},
    CHEEK: {'color': [.32, .235, .116], 'roughness': .94},
    THRESHOLD: {'color': [.55, .53, .44], 'roughness': .81},
}
GLASS_Y = 1.20
LABEL = 'Courtyard entrance / '


def _panel(b, frame, pixels, front, back, material, name, measured_plane=None):
    """Extrude a measured polygon, holding its cut outline at the surveyed plane."""
    y = front if measured_plane is None else measured_plane
    profile = [frame.plane(pixel, y) for pixel in pixels]
    signed = sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(profile, profile[1:]+profile[:1]))
    if signed < 0:
        profile.reverse()
    n = len(profile)
    vertices = [frame.xyz(x, depth, z) for depth in (front, back) for x,z in profile]
    faces = [tuple(range(n)), tuple(reversed(range(n, 2*n)))]
    faces.extend((i,n+i,n+(i+1)%n,(i+1)%n) for i in range(n))
    b.add(vertices, faces, material=material, label=LABEL+name)


def _rect(b, frame, box, front, back, material, name, measured_plane=None):
    u,v,r,t = box
    _panel(b,frame,[(u,v),(r,v),(r,t),(u,t)],front,back,material,name,measured_plane)


def _tube(b, frame, p, q, radius, material, name, sides):
    p,q = np.asarray(p,dtype=float),np.asarray(q,dtype=float)
    axis=(q-p)/np.linalg.norm(q-p)
    reference=np.array([1.,0.,0.]) if abs(axis[0]) < .8 else np.array([0.,1.,0.])
    across=np.cross(axis,reference)
    across/=np.linalg.norm(across)
    vertical=np.cross(axis,across)
    ring=[radius*(math.cos(2*math.pi*i/sides)*across+math.sin(2*math.pi*i/sides)*vertical) for i in range(sides)]
    vertices=[frame.xyz(*(end+delta)) for end in (p,q) for delta in ring]
    faces=[tuple(reversed(range(sides))),tuple(range(sides,2*sides))]
    faces.extend((i,(i+1)%sides,sides+(i+1)%sides,sides+i) for i in range(sides))
    b.add(vertices,faces,material=material,label=LABEL+name)


def _slab(b, frame, polygon, bottom, top, material, name):
    # Counterclockwise footprint, with top and bottom joined at each corner.
    n=len(polygon)
    vertices=[frame.xyz(x,y,z) for z in (bottom,top) for x,y in polygon]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    b.add(vertices,faces,material=material,label=LABEL+name)


def _arch_recess(b, frame):
    # The bright outside arch reveals a warm left cheek and a much darker
    # overhead recess. Their actual photographed edges join two depth planes.
    front,back=.23,GLASS_Y+.42
    near_x=frame.plane((519.,860.),front)[0]
    jamb_x=frame.plane((582.8,860.),GLASS_Y)[0]
    far_x=jamb_x+(jamb_x-near_x)*(back-GLASS_Y)/(GLASS_Y-front)
    roof_z=frame.plane((682.,629.),front)[1]
    left=[(near_x-.105,front),(near_x,front),(far_x,back),(far_x-.105,back)]
    _slab(b,frame,left,frame.landing_z-.006,roof_z+.075,CHEEK,'left oblique porch reveal')
    nr=frame.plane((861.,860.),front)[0]
    fr=frame.plane((865.,860.),back)[0]
    soffit=[(near_x-.105,front),(nr,front),(fr,back),(far_x-.105,back)]
    _slab(b,frame,soffit,roof_z,roof_z+.075,INTERIOR,'shaded porch ceiling')
    _rect(b,frame,(579.,622.,866.,683.),back-.020,back+.018,INTERIOR,'upper recess beyond door head')


def add_porch_doors(b, frame, lod=False):
    """Add the glass plane, its framed recess, and fittings to a shared ENU builder."""
    for key,value in PALETTE.items():
        b.palette.setdefault(key,value)
    _arch_recess(b,frame)
    plane = GLASS_Y
    # A diffuse shadow at the back of the niche leaves a genuine gap behind the glass.
    _rect(b,frame,(583,680,865,907),plane+.43,plane+.46,INTERIOR,'recess shadow',plane)
    _rect(b,frame,(580,678,585,907),plane-.17,plane+.44,THRESHOLD,'left jamb return',plane)
    _rect(b,frame,(862,679,866,907),plane-.14,plane+.44,DARK,'right jamb return',plane)
    _rect(b,frame,(583,675,865,682),plane-.09,plane+.44,DARK,'head of the recessed opening',plane)
    _rect(b,frame,(583,906.8,864,912.5),plane-.17,plane+.12,THRESHOLD,'stone threshold',plane)
    for low,high,name in [(585.,654.,'left fixed light'),(655.6,741.35,'left glass leaf'),
                           (742.65,828.4,'right glass leaf'),(830.,862.,'right fixed light')]:
        _rect(b,frame,(low,681.6,high,906.8),plane,plane+.014,GLASS,name)
    for low,high,name in [(583.1,585.,'left frame'),(654.,655.6,'left pivot jamb'),
                           (741.45,742.4,'meeting seal'),(828.4,830.,'right pivot jamb')]:
        _rect(b,frame,(low,681.1,high,906.8),plane-.004,plane+.024,DARK,name,plane)
    _rect(b,frame,(583.4,679.6,862.5,681.7),plane-.015,plane+.035,DARK,'head rail',plane)

    # Three bright lower patches are exposed. The easternmost hinge foot lies behind stone.
    for low,high,name in [(653.8,671.8,'left jamb'),(723.,740.,'left meeting stile'),(742.4,759.,'right meeting stile')]:
        _rect(b,frame,(low,900.85,high,906.9),plane-.021,plane+.023,METAL,name+' lower patch')
    for low,high,name in [(724.6,730.9,'left patch recess'),(751.1,757.3,'right patch recess')]:
        _rect(b,frame,(low,902.15,high,904.25),plane-.023,plane-.019,DARK,name)

    sides=8 if lod else 16
    front=plane-.077
    def local(pixel,depth):
        x,z=frame.plane(pixel,depth)
        return np.array([x,depth,z])
    for u,offset,name in [(729.4,0.,'left'),(754.2,-.65,'right')]:
        levels=[769.3+offset,778.7+offset,811.2+offset,825.5+offset]
        points=[local((u,v),front) for v in levels]
        for i,(material,title,radius) in enumerate([(METAL,'upper ferrule',.021),(GRIP,'dark grip',.026),(METAL,'lower ferrule',.020)]):
            _tube(b,frame,points[i],points[i+1],radius,material,name+' pull '+title,sides)
        for v,title in [(771.0+offset,'upper foot'),(822.8+offset,'lower foot')]:
            a=local((u,v),front)
            _tube(b,frame,a,a+[0.,.078,0.],.017,METAL,name+' pull '+title,sides)
    for v,name in [(816.3,'upper locking rail'),(822.8,'lower locking rail')]:
        _tube(b,frame,local((726.0,v),front-.024),local((757.5,v-.35),front-.024),.013,DARK,name,sides)
    _rect(b,frame,(756.1,816.0,758.9,823.7),front-.041,front-.001,METAL,'latch keeper')
