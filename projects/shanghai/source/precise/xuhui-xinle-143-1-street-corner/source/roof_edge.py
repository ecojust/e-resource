"""Measured front eaves, small terrace coping, lane return and the white rainwater stack."""
import numpy as np
from shapely import constrained_delaunay_triangles
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

FASCIA = 'Xinlefang | oxblood eaves fascia'
GUTTER = 'Xinlefang | dark weathered roof gutter'
SOFFIT = 'Xinlefang | warm grey soffit'
FLASHING = 'Xinlefang | folded zinc coping'
TILE = 'Xinlefang | muted terracotta roof'
HIP = 'Xinlefang | weathered clay hip covers'
PIPE = 'Xinlefang | ivory painted rainwater stack'
HOPPER = 'Xinlefang | pale square rainwater heads'
RECESS = 'Xinlefang | sheltered sandy render'
PALETTE = {
    FASCIA: {'color': [.24,.068,.05], 'roughness': .72},
    GUTTER: {'color': [.063,.068,.078], 'roughness': .72},
    SOFFIT: {'color': [.55,.49,.42], 'roughness': .87},
    FLASHING: {'color': [.46,.49,.49], 'roughness': .70},
    TILE: {'color': [.34,.128,.067], 'roughness': .93},
    HIP: {'color': [.42,.17,.094], 'roughness': .90},
    PIPE: {'color': [.76,.735,.69], 'roughness': .69},
    HOPPER: {'color': [.82,.79,.73], 'roughness': .71},
    RECESS: {'color': [.51,.43,.31], 'roughness': .88},
}
FRONT_WALL_TOP = 10.52
LANE_WALL_TOP = (10.52, 9.72)
PARAPET_TOP = 10.18
LANE_END = 7.10
EAVE_END = -6.13
PARAPET_END = -5.65
# The surveyed bank of upright brick trim below this coping belongs to the wall.
START = -8.719
SIDE_X = 2.387
CORNER = (2.75,-.419)
FAR_CORNER = (2.75+.076*(LANE_END+.419),LANE_END)

def side_z(y):
    return FRONT_WALL_TOP-.8*y/LANE_END

def front_eave_z(x):
    return 10.89+.015*(x-CORNER[0])

def side_eave_z(y):
    return front_eave_z(CORNER[0])-.8*(y+.419)/LANE_END

def shell(b, points, thickness, material, label):
    """Solid skin above a CCW plan outline with independently measured corner heights."""
    a = np.array(points, dtype=float)
    cross=np.cross(a[1]-a[0],a[2]-a[0])
    if cross[2] < 0:
        a=a[::-1]
    n=len(a)
    v=[*a-[0,0,thickness],*a]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    b.add(v,faces,material,'Xinlefang / '+label)

def cutter(b, start, end, sa, sb, material, label):
    """Sweep matching profiles across a straight eave segment; normal faces out."""
    tangent=np.array(end)-start
    tangent=tangent/np.linalg.norm(tangent)
    normal=np.array([tangent[1],-tangent[0]])
    # All section vertices are listed in horizontal-outward / vertical-up order.
    def ring(origin, profile):
        return [(*np.add(origin,normal*d),z) for d,z in profile]
    ra,rb=ring(start, sa),ring(end,sb)
    n=len(ra)
    vertices=ra+rb
    # A trough has a concave U-shaped section. Its end plates must not span
    # the channel opening or carry overlapping triangles at the open rim.
    profile=Polygon(sa)
    order={tuple(v):i for i,v in enumerate(sa)}
    caps=[]
    for tile in constrained_delaunay_triangles(profile).geoms:
        tri=orient(tile,sign=1. if profile.exterior.is_ccw else -1.)
        caps.append(tuple(order[tuple(pt)] for pt in list(tri.exterior.coords)[:3]))
    fs=caps+[tuple(i+n for i in reversed(f)) for f in caps]
    fs.extend((i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n))
    vol=sum(np.dot(vertices[f[0]],np.cross(vertices[f[i]],vertices[f[i+1]]))
            for f in fs for i in range(1,len(f)-1))
    if vol<0:fs=[f[::-1] for f in fs]
    b.add(vertices,fs,material,'Xinlefang / '+label)

def eaves(b, p, q, h, j, label, lod):
    # Section depths are relative to the outer lip. Gutter bottom remains physical
    # and the high inside rim does not seal its open trough.
    def sweep(shape, mat, desc):
        cutter(b,np.array(p),q,[(d,h+z)for d,z in shape],[(d,j+z)for d,z in shape],
               mat,label+' / '+desc)
    sweep([(-.135,-.29),(-.02,-.29),(-.02,-.10),(-.105,-.095)],FASCIA,'red fascia')
    shape=[(-.19,-.005),(-.19,-.065),(-.125,-.15),(-.053,-.155),(-.010,-.115),(0,-.015),
           (-.022,-.009),(-.035,-.10),(-.07,-.134),(-.116,-.13),(-.167,-.060),(-.169,-.007)]
    if lod:shape=[(-.19,-.005),(-.19,-.075),(-.10,-.155),(-.008,-.12),(0,-.015),
                  (-.025,-.015),(-.035,-.105),(-.10,-.128),(-.168,-.060),(-.168,-.006)]
    sweep(shape,GUTTER,'open weather channel')

def pipework(b,lod):
    # Centres of both hoppers and the lower collar are recorded on the native 2018 image.
    # Behind the right-hand gate pier the route below the last visible pipe is unobserved.
    upper=np.array([2.530,.417,10.181])
    middle=np.array([2.521,.270,7.253])
    joint=np.array([2.515,.185,4.175])
    base=np.array([2.511,.148,3.047])
    n=9 if lod else 16
    def tube(a,rad,label,mat=PIPE):
        b.tube(a,rad,mat,n,'Xinlefang / lane rainwater / '+label)
    tube([base, (2.514,.142,3.78),joint,middle,upper],.052,'continuous downpipe')
    # The white upper offset is seen against the underside of the eaves.
    tube([upper, (2.529,.432,10.36),(2.552,.477,10.44),(2.715,.716,10.56),
          (2.735,.742,10.60)],.047,'upper bend beneath gutter')
    def head(center,label):
        x,y,z=center
        # Hollow rectangular receiving head, with a tapered solid bottom and separate walls.
        # Front face points toward the lane (+X).
        width=.230;depth=.175;h=.178;t=.015
        corners=[(-depth/2,-width/2),(depth/2,-width/2),(depth/2,width/2),(-depth/2,width/2)]
        rings=[]
        for a,s in [(-.106,.46),(-.048,1.),(.105,1.),(.105,1-2*t/width),(-.035,1-2*t/width)]:
            rings.extend([(x+u*s,y+v*s,z+a)for u,v in corners])
        fs=[(3,2,1,0),(16,17,18,19)]
        for i in range(4):
            for k in range(4):
                n0=4*k;j=(i+1)%4
                fs.append((n0+i,n0+j,n0+j+4,n0+i+4))
        b.add(rings,fs,HOPPER,'Xinlefang / lane rainwater / '+label)
    head(upper,'upper collecting head');head(middle,'middle collecting head')
    tube([(2.410,.28,7.39),(2.485,.28,7.37),(2.522,.27,7.34)],.039,'middle inlet')
    tube([(2.435,.30,4.13),(2.492,.28,4.19),joint],.031,'lower small offset')
    for i,(z,y) in enumerate([(10.32,.433),(9.18,.367),(7.45,.279),(6.04,.235),
                              (4.18,.185),(3.78,.142),(3.33,.145)]):
        x=2.50+.076*y
        tube([(x,y,z-.019),(x,y,z+.023)],.063,'socket '+str(i+1))

def add_roof_edge(b,lod=False):
    for k,v in PALETTE.items(): b.palette.setdefault(k,v)
    near=(EAVE_END,CORNER[1]); corner=CORNER; far=FAR_CORNER
    # Common joint at the two fascia noses; main street/return wall tops are shared.
    eaves(b,near,corner,front_eave_z(near[0]),front_eave_z(corner[0]),'street eaves',lod)
    eaves(b,corner,far,side_eave_z(corner[1]),side_eave_z(far[1]),'lane eaves',lod)
    front=[(*near,front_eave_z(near[0])-.278),(*corner,front_eave_z(corner[0])-.278),
           (SIDE_X+.012,.04,FRONT_WALL_TOP+.065),(PARAPET_END,.04,FRONT_WALL_TOP+.065)]
    shell(b,front,.071,SOFFIT,'street projecting soffit')
    side=[(*corner,side_eave_z(corner[1])-.278),(*far,side_eave_z(far[1])-.278),
          (SIDE_X+.076*LANE_END-.025,LANE_END,side_z(LANE_END)+.066),
          (SIDE_X+.012,.04,FRONT_WALL_TOP+.065)]
    shell(b,side,.071,SOFFIT,'lane projecting soffit')
    # Aerial photographs in 2019 and 2025 show both diagonals meeting at the
    # front of this individual roof. The ridge profile behind the fold is obscured.
    # Only the surfaces up to the photographed lane return are included.
    f1=(*near,front_eave_z(near[0])-.07);f2=(*corner,front_eave_z(corner[0])-.07)
    r1=(EAVE_END,LANE_END,side_eave_z(LANE_END)-.07);r2=(*far,side_eave_z(LANE_END)-.07)
    fold=(-2.05,2.75,12.06); back=(-1.69,LANE_END,11.73)
    faces=[([f1,f2,fold],'front triangular pitch'),([f2,r2,back,fold],'lane hip pitch'),
           ([f1,fold,back,r1],'east hip pitch')]
    for pts,label in faces:shell(b,pts,.088,TILE,label)
    for a,c,label in [(f1,fold,'east sloping arris'),(f2,fold,'lane sloping arris')]:
        b.tube([np.add(a,[0,0,.015]),np.add(c,[0,0,.015])],.060 if not lod else .055,HIP,
               7 if lod else 12,'Xinlefang / '+label)
    # Left of the eave step the street photo resolves a low silver-capped terrace
    # and a short recessed grey eave. Its unseen continuation is omitted.
    cap=Polygon([(START,-.055),(PARAPET_END,-.055),(PARAPET_END,.233),(START,.233)])
    b.plan_prism(cap,PARAPET_TOP-.023,PARAPET_TOP+.045,FLASHING,'Xinlefang / terrace folded metal cover')
    x0=-7.70;x1=PARAPET_END
    b.box(((x0+x1)/2,1.19,10.23),(x1-x0,.16,.56),RECESS,label='Xinlefang / short inset pavilion head')
    b.box(((x0+x1)/2,1.16,10.54),(x1-x0+.19,.38,.085),FLASHING,label='Xinlefang / grey inset drip')
    pipework(b,lod)
