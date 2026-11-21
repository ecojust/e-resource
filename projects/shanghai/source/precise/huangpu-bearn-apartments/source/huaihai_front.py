"""The Huaihai street elevation, its eastern curve and the stepped central skyline."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

HERE = Path(__file__).parent
PARAMS = json.loads((HERE / "parameters.json").read_text())
FONT = HERE / "fonts/BearnFront.otf"
BRICK, BUFF, CAP = "warm brown small facing tiles", "ivory rendered wall", "grey concrete ledges"
WARM, STONE = "brown brick variation", "grey stone sills"
SASH, GLASS, SHOP = "dark metal casements", "blue grey upper glazing", "street shop glazing"
ROOF, IRON, RED = "flat roof surface", "painted parapet metal", "red shop lettering"
PALETTE = {k: {"color": list(c), "roughness": r} for k,c,r in [
    (BRICK,(.45,.31,.245),.89),(WARM,(.40,.275,.221),.87),(BUFF,(.77,.702,.57),.90),
    (CAP,(.55,.548,.507),.82),(STONE,(.615,.588,.509),.81),(SASH,(.15,.16,.15),.65),
    (GLASS,(.23,.29,.30),.30),(SHOP,(.16,.23,.24),.26),(ROOF,(.43,.433,.407),.90),
    (IRON,(.34,.34,.31),.63),(RED,(.55,.112,.082),.71)]}
EAVE = 19.85
CORNER_EAVE = 23.10
FLOOR = 3.14
SHOP_TOP = 3.67
CUT_DEPTH = PARAMS["roof_cut_depth_m"]


def inward(p,q):
    tangent = np.asarray(q)-p
    length = np.linalg.norm(tangent)
    return np.array([-tangent[1],tangent[0]])/length


def offset(points,distance):
    """Use the bisector at joints so all the adjoining window and roof spans meet."""
    p=np.asarray(points,dtype=float)
    normals=[inward(a,b) for a,b in zip(p,p[1:])]
    shifted=[]
    for i,pt in enumerate(p):
        a=normals[max(0,i-1)]; b=normals[min(i,len(normals)-1)]
        mix=(a+b)/(1+np.dot(a,b))
        shifted.append(pt+distance*mix)
    return np.array(shifted)


def footprint(points,back,front=0):
    return Polygon([*offset(points,front),*reversed(offset(points,back))])


def slab(builder,points,bottom,top,back,front,material,label):
    poly=footprint(points,back,front)
    assert poly.is_valid and poly.area>.001
    builder.prism(poly,bottom,top,lambda x,y,z:(x,y,z),material,label)


def pane(face,aperture,lod,shop=False):
    x,z,X,Z=aperture.bounds; middle=(x+X)/2
    frame=aperture.buffer(-.033,join_style=2)
    inner=frame.buffer(-.062,join_style=2)
    divs=[box(middle-.025,z,middle+.025,Z)]
    if not lod:
        divs.append(box(x,Z-.42,X,Z-.372))
        if X-x>2.15:
            divs.extend(box(x+(X-x)*u-.022,z,x+(X-x)*u+.022,Z)for u in (.25,.75))
    cut=inner.difference(unary_union(divs))
    face.prism(aperture.buffer(.012,join_style=2),-.346,-.318,SHOP if shop else GLASS,"recessed glazing")
    face.prism(frame.difference(cut),-.215,-.152,SASH,"casement divisions")
    if not shop:
        face.box(middle,z-.026,X-x+.095,.064,.16,.019,STONE,"thin projecting sill")


def public_panel(builder,a,b,bottom,top,material,lod,opening_width,label,shop=False,rows=1):
    face=Facade(builder,a,b,label)
    h=top-bottom
    holes=[]
    for j in range(rows):
        low=bottom+(0.13 if shop else .66)+j*h/rows
        aperture=box(-opening_width/2,low,opening_width/2,low+(h-.55 if shop else min(1.91,h/rows-.88)))
        holes.append(aperture)
    face.wall(bottom,top,holes,.38,material)
    for ap in holes:pane(face,ap,lod,shop)
    return face


def back_and_ends(builder,points,low,high,front,back):
    f=offset(points,front);r=offset(points,back)
    for a,b in zip(r[:0:-1],r[-2::-1]):
        Facade(builder,a,b,"Rear cut face").wall(low,high,(),.17,BUFF)
    for a,b in ((r[0],f[0]),(f[-1],r[-1])):
        Facade(builder,a,b,"End of illustrated section").wall(low,high,(),.17,BUFF)


def rounded_and_straight_bays():
    vertices=np.asarray(PARAMS["outer_front"],dtype=float)
    counts=[2,1,2,2,11,4]
    pts=[vertices[0]]
    for i,(a,b,n) in enumerate(zip(vertices,vertices[1:],counts)):
        pts.extend(a+(b-a)*v/n for v in range(1,n+1))
    return np.array(pts)


def oriel_panel(builder,a,b,lod,index):
    """A shallow three-sided bay keeps actual glass in its angled side lights."""
    a,b=np.asarray(a),np.asarray(b); normal=inward(a,b); edge=b-a
    front=[a,a+.19*edge-.49*normal,b-.19*edge-.49*normal,b]
    for j,(l,r) in enumerate(zip(front,front[1:])):
        length=np.linalg.norm(r-l)
        public_panel(builder,l,r,SHOP_TOP,EAVE,BRICK if j==1 else WARM,lod,max(.33,length*(.69 if j==1 else .58)),f"Projecting bay {index} face {j}",rows=5)
    outline=Polygon([*front,b+.03*normal,a+.03*normal])
    for z in (SHOP_TOP,EAVE):
        builder.prism(outline,z-.095,z+.045,lambda x,y,h:(x,y,h),CAP,"Bay cap and soffit")


def ground_and_standard_storeys(builder,points,lod):
    for i,(a,b) in enumerate(zip(points,points[1:])):
        width=np.linalg.norm(b-a)
        public_panel(builder,a,b,0,SHOP_TOP,BUFF,lod,width*.79,f"Shop bay {i+1}",True)
        if i in (1,3,5,9,12,14,16,19,21):
            oriel_panel(builder,a,b,lod,i+1)
        else:
            material=BUFF if i in (0,2,4,7,10,13,15,18,20) else BRICK
            f=public_panel(builder,a,b,SHOP_TOP,EAVE,material,lod,width*(.49 if i<7 else .55),f"Apartment bay {i+1}",rows=5)
            if material==BRICK and not lod:
                for z in (7.12,10.36,13.59,16.83):
                    f.box(0,z,min(width*.37,1.20),.12,.065,.021,WARM,"Brick spandrel course")
    back_and_ends(builder,points,0,EAVE,0,CUT_DEPTH)
    slab(builder,points,0,.10,CUT_DEPTH,0,STONE,"Closed underside")
    slab(builder,points,SHOP_TOP-.12,SHOP_TOP+.11,.75,-.63,CAP,"Broad shop canopy")
    slab(builder,points,EAVE-.37,EAVE+.20,CUT_DEPTH,-.40,CAP,"Continuous main cornice")
    slab(builder,points,EAVE+.18,EAVE+.24,CUT_DEPTH,-.035,ROOF,"Street wing roof")


def attic(builder,spine,from_depth,to_depth,bottom,top,lod,corner=False):
    visible=offset(spine,from_depth)
    for i,(a,b) in enumerate(zip(visible,visible[1:])):
        width=np.linalg.norm(b-a)
        public_panel(builder,a,b,bottom,top,BUFF if corner else (BRICK if i%3 else BUFF),lod,
                     width*(.81 if corner else .63),("Curved top floor " if corner else "Stepped upper bay ")+str(i+1))
    back_and_ends(builder,spine,bottom,top,from_depth,to_depth)
    slab(builder,spine,top-.38,top+.18,to_depth,from_depth-.32,CAP,"Upper floor eaves")
    slab(builder,spine,top+.18,top+.23,to_depth,from_depth-.04,ROOF,"Setback flat roof")


def front(builder,lod):
    points=rounded_and_straight_bays()
    ground_and_standard_storeys(builder,points,lod)
    # The round-ended part has a single glazed attic. The crown rises in two further steps.
    attic(builder,points[:10],.93,CUT_DEPTH,EAVE+.21,CORNER_EAVE,lod,True)
    attic(builder,points[9:19],.60,CUT_DEPTH,EAVE+.21,CORNER_EAVE,lod)
    attic(builder,points[10:18],1.72,CUT_DEPTH,CORNER_EAVE+.21,26.31,lod)
    attic(builder,points[11:17],2.77,CUT_DEPTH,26.52,29.49,lod)
    crown=points[13:15]
    attic(builder,crown,3.20,7.85,29.7,31.65,lod)
    slab(builder,crown,31.65,31.96,8.07,2.94,CAP,"Central stepped cap")
    for idx in (12,14,16):
        # Slender vertical piers survive between the continuous seven- and eight-storey ledges.
        axis=points[idx]; v=inward(points[idx-1],points[idx+1]); c=axis-.13*v
        builder.box((*c,21.45),(.35,.36,3.40),BUFF,label="Upper spandrel pier")
        c=axis+.97*v
        builder.box((*c,24.64),(.32,.32,3.26),BUFF,label="Setback pier continuation")
    center=offset(crown,3.75).mean(axis=0)
    for dx in (-1.35,0.,1.35):
        x,y=center+[dx,0];z=31.95;r=.22 if dx else .50;h=.43 if dx else 1.34
        vertices=[(x-r,y-r,z),(x+r,y-r,z),(x+r,y+r,z),(x-r,y+r,z),(x,y,z+h)]
        builder.add(vertices,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(0,2,1),(0,3,2)],CAP,
                    "Central rooftop finial" if dx==0 else "Flanking rooftop finials")
    builder.tube([(*center,31.96),(*center,34.02)],.037,IRON,6,"Mast above central parapet")
    # The low sign support is a separate period addition visible on the 2014 photograph.
    sign=offset(points[11:17],1.95); fascia=Facade(builder,sign[0],sign[-1],"Shop name above stepped bays")
    fascia.box(0,28.86,fascia.length,.91,.12,.02,BUFF,"Ivory sign fascia")
    add_facade_lettering(fascia,"上海市妇女用品商店",0,28.84,fascia.length*.92,.76,.087,.13,RED,label="Roof shop sign",font=FONT)
