"""No. 1 garden entrance details read from photograph 03, including the stone landing inlay."""
from math import cos, pi, sin
from pathlib import Path
import json
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union
from courtyard_portico import turned
from garden_front import INLAY,OAK,ROOM
from photo_architecture import Facade

HERE=Path(__file__).absolute().parents[1]/'measurements'
URN='Fudefang | patinated planter'
LEAF='Fudefang | dark green foliage'
LEAF_LIGHT='Fudefang | upper foliage'
PEARL='Fudefang | pale inlay chips'
GLOBE='Fudefang | warm entrance glass'
REFLECTION='Fudefang | amber on framed panel'
METAL='Fudefang | bronze door leading'
PALETTE={URN:dict(color=[.24,.213,.116],metallic=.35,roughness=.75),
         LEAF:dict(color=[.081,.126,.075],roughness=.90),
         LEAF_LIGHT:dict(color=[.115,.161,.10],roughness=.90),
         PEARL:dict(color=[.64,.65,.62],roughness=.83),
         GLOBE:dict(color=[1.,.862,.48],roughness=.34),
         REFLECTION:dict(color=[.64,.454,.20],roughness=.42),
         METAL:dict(color=[.284,.242,.195],metallic=.42,roughness=.54)}

def ring(b,x,y,r0,r1,z,t,mat,label,n):
    b.plan_prism(Point(x,y).buffer(r1,quad_segs=n).difference(Point(x,y).buffer(r0,quad_segs=n)),
                 z,z+t,mat,label)

def landing_inlay(b,z,lod):
    x,y=.004,.306
    n=12 if lod else 28
    ring(b,x,y,.35,.39,z+.0007,.0017,INLAY,'Landing | circular inlay perimeter',n)
    ring(b,x,y,.109,.133,z+.0007,.0017,INLAY,'Landing | inner annulus',n)
    petals=[]
    center=np.array([x,y])
    for i in range(8):
        a=i*pi/4;u=np.array([cos(a),sin(a)]);v=np.array([-sin(a),cos(a)])
        petals.append(Polygon([center+.061*u,center+.19*u-.045*v,center+.315*u,
                               center+.19*u+.045*v]))
        petals.append(Point(*(center+.279*np.array([cos(a+pi/8),sin(a+pi/8)]))).buffer(.021,quad_segs=5))
    b.plan_prism(unary_union(petals),z+.0011,z+.0031,INLAY,'Landing | eight petals and stone chips')
    # The lower corners of photo 03 show a darker curved band within the actual top tread.
    theta=np.linspace(-pi*.49,pi*.49,32 if lod else 68)
    def arc(rx,ry):return [(.013+rx*sin(a),.7807-ry*cos(a)) for a in theta]
    b.plan_prism(Polygon([*arc(1.869,1.887),*reversed(arc(1.683,1.693))]),
                 z+.0007,z+.0024,INLAY,'Landing | darker curved band')
    for a in np.linspace(-pi*.46,pi*.46,17 if lod else 33):
        c=np.array([.013+1.769*sin(a),.7807-1.785*cos(a)])
        u=np.array([cos(a),sin(a)]);v=np.array([-sin(a),cos(a)])
        tile=Polygon([c+.041*u,c+.033*v,c-.041*u,c-.033*v])
        b.plan_prism(tile,z+.0026,z+.0037,PEARL,'Landing | pale stones in the band')


def planter(b,x,y,z,lod,hand):
    n=12 if lod else 24
    name='Entry | '+hand+' planter'
    b.box((x,y,z+.024),(.273,.25,.048),URN,label=name+' plinth')
    profile=[(.128,.048),(.113,.089),(.101,.106),(.081,.134),(.083,.189),(.091,.202),
             (.116,.219),(.148,.244),(.148,.265),(.120,.292),(.125,.403),
             (.153,.457),(.167,.467),(.160,.487)]
    turned(b,x,y,[(r,z+h) for r,h in profile],n,URN,name+' flared vessel')
    if not lod:
        for i in range(10):
            a=2*pi*i/10
            points=[(x+(r+.003)*cos(a+d), y+(r+.003)*sin(a+d),z+h)
                    for r,h,d in [(.120,.301,-.06),(.132,.369,.02),(.146,.425,.07)]]
            b.tube(points,.007,URN,sides=5,label=name+' raised fluting')
    # Only a clipped, rounded leafy silhouette is documented. The individual leaves are indicative.
    radii=[(.484,.135),(.526,.200),(.580,.226),(.636,.205),(.684,.142),(.704,.032)]
    vertices=[]
    for j,(h,r) in enumerate(radii):
        for i in range(n):
            a=2*pi*i/n
            bump=1+.055*cos(5*a+.6*j)+.035*sin(7*a-j*.2)
            vertices.append((x+r*bump*cos(a),y+.87*r*bump*sin(a),z+h+.010*sin(3*a+.4*j)))
    faces=[tuple(reversed(range(n))),tuple(range((len(radii)-1)*n,len(radii)*n))]
    for j in range(len(radii)-1):
        for i in range(n):
            a=j*n+i;c=j*n+(i+1)%n
            faces.append((a,c,c+n,a+n))
    b.add(vertices,faces,LEAF,name+' clipped foliage')
    if not lod:
        for i in range(13):
            a=2*pi*i/13
            px=x+.14*cos(a);py=y+.125*sin(a)
            turned(b,px,py,[(.036,z+.645),(.048,z+.673),(.030,z+.701),(.008,z+.712+.01*cos(5*a))],
                   6,LEAF_LIGHT,name+' irregular upper foliage')

def entry_light(b,lod):
    n=10 if lod else 20
    # A second amber patch appears within a framed field beyond the pendant.
    # Its depth and whether it is a reflection are indeterminate in the original.
    x,y=.0898,2.88
    turned(b,x,y,[(.009,2.63),(.009,3.18)],n,METAL,'Entrance | pendant suspension')
    turned(b,x,y,[(.012,2.464),(.032,2.478),(.045,2.527),(.061,2.542),(.069,2.607),
                   (.055,2.647),(.023,2.655)],n,GLOBE,'Entrance | photographed warm glass pendant')
    back=Facade(b,(-.48,3.015),(.66,3.015),'Vestibule | framed field')
    for u in (-.255,.255):back.box(u,2.288,.027,.302,.031,0.,OAK,'side')
    for h in (2.137,2.439):back.box(0,h,.54,.025,.031,0.,OAK,'rail')
    turned(b,.09,2.975,[(.009,2.228),(.043,2.258),(.049,2.297),(.032,2.315)],n,REFLECTION,
           'Vestibule | amber shape visible in framed field')
    # Flush bottom of the round ceiling fitting under the front balcony, distinct from the indoor lamp.
    p=(.014,.035)
    turned(b,*p,[(.083,3.715),(.109,3.745),(.123,3.777),(.123,3.806)],n,METAL,
           'Portico | circular ceiling fitting')

def sidelights(b,lod):
    front=Facade(b,(-2.28,1.596),(2.28,1.596),'Entrance | patterned door glazing')
    for hand in (-1,1):
        u=hand*.77
        polygons=[]
        for z,h in [(1.02,.14),(2.47,.105)]:
            polygons.append(LineString([(u-.095,z),(u,z+h),(u+.095,z),(u,z-h),(u-.095,z)]).buffer(.009,join_style=2))
        for sign in (-1,1):
            polygons.append(LineString([(u+sign*.10,1.01),(u+sign*.043,1.18),
                                        (u+sign*.043,2.31),(u+sign*.10,2.47)]).buffer(.007,join_style=2))
        front.prism(unary_union(polygons),-.158,-.143,METAL,'lozenge and narrow leaded fields')

def add_details(b,lod=False):
    d=json.loads((HERE/'balcony-curves.json').read_bytes())['bowed_plan']
    z=d['upper_landing_z']
    landing_inlay(b,z,lod)
    planter(b,-1.57,.53,z,lod,'west')
    planter(b,1.62,.55,z,lod,'east')
    entry_light(b,lod)
    sidelights(b,lod)
