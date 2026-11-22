"""Two superimposed pairs of arched openings on the returned front of Yi Hong Garden."""
from math import cos, pi, sin, sqrt


def finish(rgb, rough=.86):
    return {'color': [((v/255+.055)/1.055)**2.4 for v in rgb], 'roughness':rough}


PALETTE={
    'lime joints':finish((154,151,142)), 'grey brick':finish((132,137,134)),
    'cool grey brick':finish((119,126,124)), 'warm grey brick':finish((142,140,129)),
    'brick ring':finish((163,100,76)), 'pale voussoir':finish((179,116,88)),
    'deep voussoir':finish((147,86,67)), 'limestone':finish((168,164,145)),
    'shaft stone':finish((141,145,132)), 'balcony iron':finish((59,67,62),.47),
    'shaded floor':finish((113,110,102)), 'timber fascia':finish((110,81,65)),
    'tile':finish((136,88,73)), 'sheltered soffit':finish((113,110,99)),
}
RADIUS=3.68
CENTRES=(-1.01,1.01)
SPRING=(1.66,4.42)
STORED_WIDTH=2.32
WIDTH=.815
RISE=.835


def point(u,d,z):
    theta=u/RADIUS
    return ((RADIUS-d)*sin(theta), RADIUS-(RADIUS-d)*cos(theta), z)


def prism(b, polygon, front, back, material, label):
    # Traverse the visible face counterclockwise in the developed elevation.
    n=len(polygon)
    pts=[point(u,d,z) for d in (front,back) for u,z in polygon]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces.extend((i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n))
    b.add(pts,faces,material,label)


def panel(b,left,right,base,top,front,back,material,label):
    prism(b,[(left,base),(right,base),(right,top),(left,top)],front,back,material,label)


def band(b,z0,z1,d0,d1,material,label,n=30):
    for i in range(n):
        l=-STORED_WIDTH+2*STORED_WIDTH*i/n
        r=-STORED_WIDTH+2*STORED_WIDTH*(i+1)/n
        panel(b,l,r,z0,z1,d0,d1,material,label)


def stone_supports(b,z0,z1,name):
    for i,u in enumerate((-2.02,0,2.02)):
        label=name+' pier '+str(i+1)
        for za,zb,w,d in [(z0,z0+.09,.472,-.046),(z0+.09,z0+.18,.406,-.018),
                          (z0+.18,z1-.235,.328,.012),(z1-.235,z1-.179,.362,-.004),
                          (z1-.179,z1-.078,.409,-.022),(z1-.078,z1,.477,-.048)]:
            panel(b,u-w/2,u+w/2,za,zb,d,.34,'shaft stone' if w==.328 else 'limestone',label)


def arched_wall(b,c,spring,top,lod,name):
    # Continuous masonry between the red arch extrados and the upper ledge.
    width=WIDTH+.183
    height=RISE+.165
    for i in range(40 if not lod else 22):
        segments=40 if not lod else 22
        a=pi*(1-i/segments);h=pi*(1-(i+1)/segments)
        l=c+width*cos(a);r=c+width*cos(h)
        prism(b,[(l,spring+height*sin(a)),(r,spring+height*sin(h)),(r,top),(l,top)],
              0,.305,'lime joints',name+' arch spandrel')
    for side in (-1,1):
        a=c+side*width;k=c+side*1.01
        panel(b,min(a,k),max(a,k),spring,top,0,.305,'lime joints',name+' arch spandrel')
    # Bond pattern uses physically bounded, clipped brick faces and curved bed joints.
    row=.086 if not lod else .143
    length=.192 if not lod else .308
    count=int((top-spring)/row)+1
    for j in range(count):
        za=spring+j*row+.004;zb=min(top-.002,za+row-.009)
        if zb<=za:continue
        for k in range(-9,10):
            l=max(-1.009,k*length+(j%2)*length/2+.005)
            r=min(1.009,k*length+(j%2)*length/2+length-.005)
            if r-l<.016:continue
            def lower(x):
                return max(za,spring+height*sqrt(max(0,1-(x/width)**2))+.002) if abs(x)<width else za
            points=[(c+l,lower(l))]
            for t in (.25,.5,.75,1.):
                xx=l+(r-l)*t;points.append((c+xx,lower(xx)))
            # Each cropped brick is assembled from small convex quads.
            mat=('grey brick','cool grey brick','grey brick','warm grey brick')[(j*13+k*7)%4]
            for (lx,lz),(rx,rz) in zip(points,points[1:]):
                if lz>=zb and rz>=zb:continue
                if lz>=zb:
                    lx=lx+(rx-lx)*(lz-zb)/(lz-rz);lz=zb
                if rz>=zb:
                    rx=lx+(rx-lx)*(zb-lz)/(rz-lz);rz=zb
                # Front facing quads, without zero-area wedges along the cut.
                poly=[(lx,lz),(rx,rz)]
                if rz<zb-1e-7:poly.append((rx,zb))
                if lz<zb-1e-7:poly.append((lx,zb))
                if len(poly)>2:prism(b,poly,-.004,.002,mat,name+' grey coursed spandrel')
    for i in range(23):
        a=pi*i/23;h=pi*(i+1)/23
        def arc(ang,width,height):return (c+width*cos(ang),spring+height*sin(ang))
        for lo,hi,mat,f in [(a,h,'lime joints',-.008),(a+.004,h-.004,
                         ('brick ring','deep voussoir','brick ring','pale voussoir')[i%4],-.021)]:
            steps=2 if lod else 4
            for seg in range(steps):
                a0=lo+(hi-lo)*seg/steps;a1=lo+(hi-lo)*(seg+1)/steps
                poly=[arc(a0,WIDTH,RISE),arc(a0,width,height),arc(a1,width,height),arc(a1,WIDTH,RISE)]
                prism(b,poly,f,.30,mat,name+' tapered arch bricks')


def balustrade(b,c):
    for z in (2.935,3.487,3.538):
        for i in range(12):
            left=c-.831+1.662*i/12;right=left+1.662/12
            panel(b,left,right,z,z+(.027 if z==3.538 else .019),-.008,.017,'balcony iron','curved balcony rails')
    for i in range(13):
        x=c+i*.128-.768
        panel(b,x-.010,x+.010,2.918,3.54,-.002,.013,'balcony iron','balcony square uprights')


def add_building(b,lod=False):
    band(b,0,.093,-.02,.96,'shaded floor','ground sill')
    band(b,2.716,2.793,-.043,.99,'limestone','lower balcony projection')
    band(b,2.793,2.853,-.103,.99,'limestone','main balcony shelf')
    band(b,2.853,2.909,-.055,.99,'shaded floor','balcony pavement')
    for j,(z0,spring,top) in enumerate(((.093,1.66,2.716),(2.909,4.42,5.523))):
        name=('lower','upper')[j]
        stone_supports(b,z0,spring,name)
        for i,c in enumerate(CENTRES):
            arched_wall(b,c,spring,top,lod,name+' arch '+str(i+1))
        for side in (-1,1):
            l,r=sorted((side*2.02,side*STORED_WIDTH))
            panel(b,l,r,spring,top,0,.305,'grey brick',name+' end wall return')
    for c in CENTRES:balustrade(b,c)
    for za,zb,d,mat in [(5.523,5.57,-.045,'limestone'),(5.57,5.64,-.083,'brick ring'),
                        (5.64,5.69,-.134,'timber fascia'),(5.69,5.73,-.144,'tile')]:
        band(b,za,zb,d,.40,mat,'curving roof eave')
