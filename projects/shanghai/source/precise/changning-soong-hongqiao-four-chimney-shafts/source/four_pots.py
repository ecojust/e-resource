"""Exposed four-part stack on the photographed ridge at No. 1430 Hongqiao Road."""
from math import cos,sin,pi,hypot,floor,ceil
import random

def finish(rgb,roughness=.93):
    def linear(c):
        x=c/255
        return x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb],roughness=roughness,metallic=0)
PALETTE={
 'coarse render':finish((137,118,95)),
 'exposed edge':finish((165,146,119)),
 'darker roughcast':finish((108,96,82)),
 'pale stone granule':finish((163,147,120)),
 'clay shaft':finish((115,91,74)),
 'warm clay shaft':finish((127,101,80)),
 'smoked shoulder':finish((96,80,68)),
 'raised cap course':finish((118,98,85)),
 'upper cap':finish((99,83,74)),
 'charcoal weathering':finish((88,72,62)),
 'umber clay':finish((108,87,73)),
 'buff clay':finish((124,101,83)),
 'brown weathering':finish((99,80,68)),
 'dusty clay':finish((132,107,89)),
}
POTS=(-.465,-.155,.155,.465)
def outline(cx,hx,hy,cut):
    return [(cx-hx+cut,-hy),(cx+hx-cut,-hy),(cx+hx,-hy+cut),
            (cx+hx,hy-cut),(cx+hx-cut,hy),(cx-hx+cut,hy),
            (cx-hx,hy-cut),(cx-hx,-hy+cut)]
def course(b,label,cx,za,zb,lower,upper,material):
    low=outline(cx,*lower);hi=outline(cx,*upper);n=len(low)
    v=[(x,y,za) for x,y in low]+[(x,y,zb) for x,y in hi]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((k,(k+1)%n,n+(k+1)%n,n+k)for k in range(n))
    b.add(v,faces,material,label)
def finish_patchwork(b,lod):
    # Shallow, irregular grains follow the observed granulated surface. The pattern
    # is original; the individual grains on the photograph have not been traced.
    rnd=random.Random(1430)
    for side in ('front','right','back','left'):
        half=.620 if side in ('front','back')else .234
        count=(130 if side in ('front','back') else 52) if not lod else (30 if side in ('front','back')else 12)
        verts={};faces={}
        for _ in range(count):
            mat=rnd.choice(('pale stone granule','darker roughcast','coarse render'))
            v=verts.setdefault(mat,[]);tri=faces.setdefault(mat,[])
            x=rnd.uniform(-half+.009,half-.009);z=rnd.uniform(.03,1.204);r=rnd.uniform(.003,.012)*(1.35 if lod else 1);angle=rnd.uniform(0,2*pi)
            def pos(u,h,depth):
                if side=='front':return (u,-.25-depth,h)
                if side=='right':return (.634+depth,u,h)
                if side=='back':return (-u,.25+depth,h)
                return (-.634-depth,-u,h)
            i=len(v);v.append(pos(x,z,.0035));n=3 if lod else 5
            for j in range(n):
                a=angle+2*pi*j/n;v.append(pos(x+r*cos(a),z+.66*r*sin(a),.0004))
            for j in range(n):tri.append((i,i+1+j,i+1+(j+1)%n))
        for mat in verts:b.add(verts[mat],faces[mat],mat,side+' roughcast '+mat)
def weathered_stem(b, column, center, tube, lod):
    """Tile the real flat and chamfered faces with patchy fired-clay finishes."""
    corners=outline(center,*tube)
    base='warm clay shaft' if column in (1,3) else 'clay shaft'
    z0,z1=1.324,1.979
    b.add([(x,y,z0) for x,y in corners], [tuple(reversed(range(8)))], base, 'shaft '+str(column+1)+' stem bottom')
    b.add([(x,y,z1) for x,y in corners], [tuple(range(8))], base, 'shaft '+str(column+1)+' stem top')
    rng=random.Random(1970+column)
    for edge,((x0,y0),(x1,y1)) in enumerate(zip(corners,corners[1:]+corners[:1])):
        length=hypot(x1-x0,y1-y0)
        width=max(2,ceil(length/(.039 if lod else .017)))
        height=14 if lod else 35
        lattice={(ix,iz):rng.uniform(-1,1) for ix in range(13) for iz in range(25)}
        def noise(u,v):
            i,j=floor(u),floor(v)
            a,b=u-i,v-j
            return (1-b)*((1-a)*lattice[i,j]+a*lattice[i+1,j])+b*((1-a)*lattice[i,j+1]+a*lattice[i+1,j+1])
        vertices=[]
        for j in range(height+1):
            for i in range(width+1):
                u=(i+(rng.uniform(-.25,.25) if 0<i<width else 0))/width
                v=(j+(rng.uniform(-.25,.25) if 0<j<height else 0))/height
                vertices.append((x0+u*(x1-x0),y0+u*(y1-y0),z0+v*(z1-z0)))
        faces={}
        for j in range(height):
            for i in range(width):
                a=j*(width+1)+i
                idx=(a,a+1,a+width+2,a+width+1)
                u,v=(i+.5)/width,(j+.5)/height
                tone=.52*noise(u*length*17,v*6)+.30*noise(u*length*33,v*14)+.18*rng.uniform(-1,1)
                material='charcoal weathering' if tone<-.53 else 'brown weathering' if tone<-.33 else 'umber clay' if tone<-.13 else 'dusty clay' if tone>.48 else 'buff clay' if tone>.21 else base
                faces.setdefault(material,[]).append(idx)
        for material,polygons in faces.items():
            used=sorted({n for polygon in polygons for n in polygon});indices={n:i for i,n in enumerate(used)}
            b.add([vertices[n] for n in used],[tuple(indices[n]for n in poly) for poly in polygons],material,'shaft '+str(column+1)+' patinated clay')

def add_building(b,lod=False):
    base=(.634,.250,.010);shoulder=(.699,.303,.013)
    course(b,'exposed common chimney breast',0,.009,1.222,base,base,'coarse render')
    finish_patchwork(b,lod)
    course(b,'overhanging shoulder underside',0,1.222,1.251,shoulder,shoulder,'smoked shoulder')
    course(b,'bevel shedding rain from stack',0,1.251,1.353,shoulder,(.626,.238,.014),'exposed edge')
    for i,c in enumerate(POTS):
        text='shaft '+str(i+1)+' '
        tube=(.145,.217,.053);cap0=(.153,.224,.057);cap1=(.154,.247,.062)
        weathered_stem(b,i,c,tube,lod)
        course(b,text+'stepped base of collar',c,1.979,2.019,tube,cap1,'smoked shoulder')
        course(b,text+'first proud band',c,2.019,2.096,cap1,cap1,'raised cap course')
        course(b,text+'recessed joint beneath upper cap',c,2.096,2.117,cap0,cap0,'smoked shoulder')
        course(b,text+'upper drip lip',c,2.117,2.146,cap0,cap1,'smoked shoulder')
        course(b,text+'cut-corner top course',c,2.146,2.247,cap1,(.150,.239,.060),'upper cap')
        if not lod:
            course(b,text+'liner below the first cap',c,1.930,1.943,(.146,.219,.053),(.146,.219,.053),'clay shaft')
