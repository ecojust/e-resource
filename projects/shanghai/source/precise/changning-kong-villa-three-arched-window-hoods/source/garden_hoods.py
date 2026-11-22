"""Three canopies on the garden wall of the Kung villa, modelled from the 2018 captioned photograph."""
from math import cos, sin, pi

def pigment(rgb):
    def linear(c):
        v=c/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb],roughness=.91,metallic=0)
PALETTE={name:pigment(rgb) for name,rgb in {
 'lime wall':(216,218,211), 'ivory hood':(222,220,208), 'curved soffit':(183,188,184),
 'rounded hood edge':(234,226,202), 'bracket stucco':(212,210,194),'shadow joint':(167,161,146),
 'window surround':(228,225,207),'weathered apron':(200,193,176)}.items()}
BAYS=[(-1.085,.482,.289,.539,1.14),(0,.593,.815,.736,1.177),(1.085,.482,.289,.539,1.14)]
SUPPORTS=[(-1.575,.54),(-.589,.735),(.589,.735),(1.575,.54)]

def cuboid(b,name,x0,x1,y0,y1,z0,z1,mat):
    v=[(x,y,z)for z in (z0,z1)for y in (y0,y1)for x in (x0,x1)]
    b.add(v,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(1,3,7,5),(3,2,6,7),(2,0,4,6)],mat,name)

def curved_strip(b, name, x, spring, r, height, depth, n, shell=True):
    thickness=.045
    rings=[]
    for j in range(n+1):
        theta=pi*j/n
        rings.append([(x+(r+d)*cos(theta),y,spring+(height+d)*sin(theta))
                      for d,y in [(0,-depth),(0,.026),(thickness,.026),(thickness,-depth)]])
    v=sum(rings,[])
    # The barrel has a separate surface material on the inside and a readable rim.
    for k,mat,part in [(0,'curved soffit','vault underside'),(1,'ivory hood','rear edge'),(2,'ivory hood','outer crown'),(3,'rounded hood edge','front arch edge')]:
        faces=[(4*(j+1)+k,4*(j+1)+(k+1)%4,4*j+(k+1)%4,4*j+k)for j in range(n)]
        b.add(v,faces,mat,name+' '+part)
    b.add(v,[(0,1,2,3),(4*n+3,4*n+2,4*n+1,4*n)],'weathered apron',name+' closed eaves')
    # A rounded painted arris along the outer face catches the light on the
    # source photograph. It is integral to the plaster, never an applied photo.
    radial_steps=7 if shell else 4
    beads=[]
    for j in range(n+1):
        a=pi*j/n
        nx,nz=cos(a)/(r+thickness),sin(a)/(height+thickness)
        norm=(nx*nx+nz*nz)**.5;nx/=norm;nz/=norm
        xx=x+(r+thickness-.006)*cos(a);zz=spring+(height+thickness-.006)*sin(a)
        for k in range(radial_steps):
            phi=2*pi*k/radial_steps
            beads.append((xx+.009*nx*cos(phi),-depth-.002-.009*sin(phi),zz+.009*nz*cos(phi)))
    f=[]
    for j in range(n):
        for k in range(radial_steps):
            u=j*radial_steps+k;v0=j*radial_steps+(k+1)%radial_steps
            f.append((u,u+radial_steps,v0+radial_steps,v0))
    b.add(beads,f,'rounded hood edge',name+' plaster lip')
    for s,side in [(-1,'left'),(1,'right')]:
        xx=x+s*(r+.0225)
        cuboid(b,name+' '+side+' spring course',xx-.041,xx+.041,-depth-.012,.036,spring-.036,spring+.005,'rounded hood edge')
        if shell:
            cuboid(b,name+' '+side+' shadow at spring',xx-.036,xx+.036,-depth,.029,spring-.047,spring-.035,'shadow joint')

def bracket(b, index, x, projection, lod):
    segments=10 if lod else 25
    # A low wall heel expands forward into the outer seat of the arch.
    profile=[(-.115,.175)]
    for i in range(segments+1):
        t=i/segments
        y=-(.115+(projection-.115)*(t*t*(.61+.39*t)))
        z=.217+.855*(1-(1-t)**2.0)
        profile.append((y,z))
    profile.append((-projection,1.135))
    half=.065
    verts=[]
    for y,z in profile:
        verts.extend([(x-half,y,z),(x+half,y,z),(x+half,.027,z),(x-half,.027,z)])
    faces=[(3,2,1,0)]
    for j in range(len(profile)-1):
        for k in range(4):
            a=4*j+k;bside=4*j+(k+1)%4
            faces.append((a,bside,bside+4,a+4))
    u=4*(len(profile)-1)
    faces.append((u,u+1,u+2,u+3))
    b.add(verts,faces,'bracket stucco','curved support '+str(index))
    for j,(width,front,bottom,top) in enumerate([(.177,.150,.125,.156),(.194,.167,.156,.175),(.177,.149,.175,.202)]):
        cuboid(b,'support '+str(index)+' heel moulding '+str(j),x-width/2,x+width/2,-front,.04,bottom,top,'window surround')
    cuboid(b,'support '+str(index)+' upper bed',x-.094,x+.094,-projection-.009,.047,1.1,1.142,'window surround')
    # Some draft edges remain at both resolutions along the upright.
    if not lod:
        cuboid(b,'support '+str(index)+' heel shadow',x-.076,x+.076,-.137,.025,.118,.125,'shadow joint')

def add_building(b,lod=False):
    cuboid(b,'wall panel behind the crowns',-1.725,1.725,.028,.179,1.04,2.216,'lime wall')
    for i,(x,d) in enumerate(SUPPORTS):
        cuboid(b,'window jamb '+str(i),x-.093,x+.093,.017,.18,.014,1.047,'window surround')
        bracket(b,i+1,x,d,lod)
    for i,(cx,r,h,d,z) in enumerate(BAYS):
        curved_strip(b,'hood '+str(i+1),cx,z,r,h,d,(22 if lod else 60),not lod)
