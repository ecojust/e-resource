"""Twin ground-floor arches visible on the corner end of the experts' villa veranda."""
from math import cos,sin,pi,radians
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
PALETTE={
    'rough cream render':dict(color=[.615,.565,.455],roughness=.96),
    'warm intrados render':dict(color=[.481,.423,.315],roughness=.98),
    'grey dressed stone':dict(color=[.326,.311,.283],roughness=.9),
    'granite facet in light':dict(color=[.382,.365,.335],roughness=.99),
    'granite facet in shade':dict(color=[.225,.223,.207],roughness=.98),
    'dark grey spring bed':dict(color=[.239,.236,.215],roughness=.94),
    'cream cornice':dict(color=[.792,.755,.66],roughness=.86)
}
RADIUS=1.16
SPRING=1.80
CENTRES=(-1.38,1.38)
X0=-2.76
X1=2.76
DEPTH=.43
TOP=3.81

def face_solid(b,poly,front,back,mat,label):
    # Keep the front skin facing a viewer on the garden side, y<0.
    b.prism(poly,-back,-front,lambda x,z,ny:(x,-ny,z),mat,label)

def arch_opening(x,segments):
    perimeter=[(x-RADIUS,-.025),(x+RADIUS,-.025),(x+RADIUS,SPRING)]
    perimeter.extend((x+RADIUS*cos(i*pi/segments),SPRING+RADIUS*sin(i*pi/segments)) for i in range(1,segments+1))
    return Polygon(perimeter)

def wedge_points(center,ang,half,reach):
    # The photo shows separate radial blocks, with render between them.
    pts=[(RADIUS+.023,ang-half),(RADIUS+reach*.80,ang-half-.5),(RADIUS+reach,ang+half*.04),(RADIUS+reach*.83,ang+half+.8),(RADIUS+.023,ang+half)]
    return [(center+r*cos(radians(a)),SPRING+r*sin(radians(a)))for r,a in pts]

def rough_block(b,polygon,depth,label,seed,far):
    pts=list(polygon.exterior.coords)[:-1]
    if Polygon(pts).area<=0:return
    front=[]
    for i,(x,z) in enumerate(pts):
        noise=(((seed+i*7)*31)%19)/19
        front.append((x,-depth*(.69+.26*noise),z))
    back=[(x,.009,z) for x,z in pts]
    if Polygon(pts).exterior.is_ccw is False:
        front.reverse();back.reverse()
    count=len(front);c=polygon.representative_point()
    tip=(c.x,-depth*(.99 if far else 1.07),c.y)
    for i in range(count):
        j=(i+1)%count
        b.add([back[i],back[j],front[j],front[i]],[(0,1,2,3)],'grey dressed stone',label+' jamb')
        material=('grey dressed stone','granite facet in light','grey dressed stone','granite facet in shade')[(seed+i)%4]
        b.add([front[i],front[j],tip],[(0,1,2)],material,label+' lit face')
    b.add(back,[tuple(reversed(range(count)))],'grey dressed stone',label+' bed')

def build_veranda(b,lod):
    seg=24 if lod else 54
    apertures=unary_union([arch_opening(x,seg) for x in CENTRES])
    plane=box(X0,0,X1,TOP).difference(apertures)
    face_solid(b,plane,0,.02,'rough cream render','two arches central and terminal piers')
    face_solid(b,plane,.02,DEPTH,'warm intrados render','veranda arch reveals')
    # Two outside half piers and the full shared pier carry separate spring stones.
    for k,c in enumerate((X0,0,X1)):
        left=max(X0,c-.245);right=min(X1,c+.245)
        face_solid(b,box(left,SPRING-.118,right,SPRING-.073),-.069,.007,'dark grey spring bed',f'spring bed {k}')
        mid=(left+right)/2
        poly=Polygon([(left,SPRING-.071),(right,SPRING-.071),(right,SPRING+.072),(mid+.1*(right-left),SPRING+.133),(left,SPRING+.089)])
        rough_block(b,poly,.105,'spring block '+str(k),k+5,lod)
    for k,x in enumerate(CENTRES):
        for i,angle in enumerate((23,55,126,153)):
            pts=wedge_points(x,angle,5.5 if i in (0,3)else 6.3,.275 if i in (0,3)else .31)
            rough_block(b,Polygon(pts),.112,f'arch {k} grey radial block {i}',i+3*k,lod)
        # Three adjacent stones form the large crown wedge seen on both arches.
        for j,(ang,half,reach) in enumerate([(82.9,3.0,.39),(90.0,4.0,.50),(97.1,3.0,.39)]):
            rough_block(b,Polygon(wedge_points(x,ang,half,reach)),.143,f'arch {k} three-part key {j}',8-j+k,lod)
    for i,(z0,z1,d) in enumerate([(3.71,3.743,.037),(3.743,3.778,.082),(3.778,3.81,.114)]):
        face_solid(b,box(X0,z0,X1,z1),-d,0,'cream cornice',f'cornice member {i}')
