"""Pierced cast-stone parapet of the attic terrace and growth on the north street wall."""
from math import pi, sin, cos
from random import Random
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from villa_materials import BALUST, BASE, IRON, LEAVES, SILL, STONE, VINE
from villa_roof import DECK, HALF_DEPTH
from villa_walls import GALLERY_FRONT, GALLERY_HALF, NORTH, PLAN_SCALE
from villa_windows import circle


def balustrade(face,central,lod):
    half=face.length/2
    piers=[-half,0,half] if central else [-half,half]
    for u in piers:
        face.box(u,DECK+.53,.275,1.06,.29,-.005,BALUST,'balustrade square pier')
        face.box(u,DECK+1.075,.325,.065,.34,.0,SILL,'pier weathering')
        face.box(u,DECK+1.129,.370,.047,.382,.0,STONE,'overhanging cap')
    for l,r in zip(piers,piers[1:]):
        left=l+.128;right=r-.128;width=right-left;mid=(l+r)/2
        face.box(mid,DECK+.20,width,.40,.23,-.01,BALUST,'solid terrace curb')
        face.box(mid,DECK+.452,width,.104,.255,-.01,STONE,'curb coping')
        face.box(mid,DECK+.892,width,.115,.209,-.012,BALUST,'balustrade upper rail')
        face.box(mid,DECK+.982,width+.03,.075,.27,-.01,STONE,'balustrade upper cap')
        # The frieze has pointed necks above and below a central pierced diamond,
        # plainly visible against sky in the post-restoration garden elevation.
        cells=max(3,round(width/.318))
        step=width/cells
        shapes=[]
        for j in range(cells):
            u=left+(j+.5)*step; a=step*.50
            outline=Polygon([(u-.056,DECK+.49),(u+.056,DECK+.49),
                (u+.041,DECK+.566),(u+a,DECK+.635),(u+a,DECK+.694),
                (u+.045,DECK+.755),(u+.066,DECK+.84),(u-.066,DECK+.84),
                (u-.045,DECK+.755),(u-a,DECK+.694),(u-a,DECK+.635),(u-.041,DECK+.566)])
            eye=circle(u,DECK+.665,.035,10 if lod else 18)
            shapes.append(outline.difference(eye))
        face.prism(unary_union(shapes),-.068,.071,BALUST,'open diamond stone balusters')


def terrace_and_porch(builder,lod):
    x=GALLERY_HALF;y=GALLERY_FRONT
    balustrade(Facade(builder,(-x,y),(x,y),'south terrace front'),True,lod)
    # The photograph looking down into the terrace shows two short side returns.
    for side in (-1,1):
        a,b=((x,y),(x,-HALF_DEPTH)) if side==1 else ((-x,-HALF_DEPTH),(-x,y))
        balustrade(Facade(builder,a,b,'south terrace return'),False,lod)
    for a,b in ((-x+.28,-.34),(.34,x-.28)):
        y0=y-.15
        for xx in (a,(a+b)/2,b):
            builder.tube([(xx,y0,.12),(xx,y0,.96)],.020,IRON,6 if lod else 9,'garden porch guard posts')
        for h in (.29,.78,.965):
            builder.tube([(a,y0,h),(b,y0,h)],.015 if h<.90 else .022,IRON,6 if lod else 9,'garden porch guard rails')


def street_ivy(face,lod):
    rng=Random(5172018)
    skip=[]
    for (bottom,top),features in zip(((.57,2.20),(3.84,6.20),(7.39,9.73)),NORTH):
        for a,b in features:
            l=(668-b)*PLAN_SCALE;r=(668-a)*PLAN_SCALE
            skip.append((l-.07,r+.07,bottom,top))
    def allowed(u,z):
        return -8.86<u<8.86 and not any(a<u<b and low<z<high for a,b,low,high in skip)
    verts=[[]for _ in LEAVES];faces=[[]for _ in LEAVES]
    def leaf(u,z,size,lean):
        mat=rng.randrange(3);v=verts[mat];k=len(v)
        profile=[(0,size*.85),(.61*size,.21*size),(.69*size,-.32*size),
                 (.23*size,-.42*size),(0,-size),(-.76*size,-.25*size),(-.65*size,.30*size)]
        distance=.046+rng.random()*.067
        for du,dz in profile:
            v.append(face.point(u+du*cos(lean)-dz*sin(lean),z+du*sin(lean)+dz*cos(lean),distance))
        v.append(face.point(u,z,distance+size*.18))
        faces[mat].extend((k+(j+1)%7,k+j,k+7)for j in range(7))
    def curtain(u,z,radius,height,mat):
        # Overlapping mats of ivy form the solid green masses visible around the
        # centre windows. Their irregular edges are scalloped, including in the LOD.
        points=[]
        corners=19 if lod else 29
        depth=rng.uniform(.040,.062)
        for k in range(corners):
            angle=2*pi*k/corners
            size=max(.70,1+.10*sin(angle*5)+.15*sin(angle*9+.6)+rng.uniform(-.09,.08))
            points.append((u+radius*cos(angle)*size,z+height*sin(angle)*size))
        clipped=Polygon(points)
        for l,r,low,high in skip:
            if u+radius*1.35>=l and u-radius*1.35<=r and z+height*1.35>=low and z-height*1.35<=high:
                clipped=clipped.difference(box(l,low,r,high))
        # Use actual outward depth and real edges; the leaf blades sit in front.
        if not clipped.is_empty:
            face.prism(clipped,depth-.017,depth,LEAVES[mat],'dense north ivy curtains')
    # Coordinates follow the heavier curtains beside the central group. The westmost
    # and eastmost gable lights remain readable from street level.
    for index,(base,top,width) in enumerate(((-7.25,10.15,.54),(-4.62,9.97,1.14),
                    (-2.42,10.36,.97),(-.60,6.73,.61),(2.62,10.15,1.13),(4.04,10.54,.88),(6.89,7.53,.53))):
        phase=index*1.76
        def spine(z):return base+.28*sin(.81*z+phase)+.15*sin(1.43*z+phase)
        zs=[.24+i*.41 for i in range(int((top-.24)/.41)+1)]
        points=[face.point(spine(z),z,.042)for z in zs]
        face.builder.tube(points,.027 if lod else .033,VINE,5 if lod else 7,'north elevation climbing stems')
        # The 2018 street elevation has substantial curtains on the two sides
        # of its central bays. Outer gables retain narrower strands.
        spread=[.54,1.24,1.10,.60,1.08,1.03,.46][index]
        nr=int(top*(1.30 if lod else 1.85))
        for j in range(nr):
            z=.68+(top-.75)*(j+.35)/nr
            envelope=.53+.50*sin(pi*min(1,z/top))+.14*sin(z*1.9+phase)
            u=spine(z)+rng.uniform(-.38,.38)*spread
            curtain(u,z,spread*envelope*rng.uniform(.58,.91),rng.uniform(.48,.75),rng.choice((0,2,2)))
        for j in range(int(top*(4.0 if lod else 10.8))):
            z=rng.uniform(.29,top);u=spine(z)+width*rng.uniform(-1,1)
            if allowed(u,z):
                leaf(u,z,rng.uniform(.105,.186) if lod else rng.uniform(.066,.15),rng.uniform(-.8,.8))
                if not lod:
                    for k in range(2):
                        du=rng.uniform(-.105,.105);dz=rng.uniform(-.12,.12)
                        if allowed(u+du,z+dz):leaf(u+du,z+dz,rng.uniform(.057,.13),rng.uniform(-1,1))
            if j%8==0 and allowed(u,z) and allowed(spine(z),z):
                face.builder.tube([face.point(spine(z),z-.14,.044),face.point(u,z,.056)],.012,VINE,5,'ivy side shoots')
    for p,f,mat in zip(verts,faces,LEAVES):
        if p:face.builder.add(p,f,mat,'north street ivy leaf blades')
