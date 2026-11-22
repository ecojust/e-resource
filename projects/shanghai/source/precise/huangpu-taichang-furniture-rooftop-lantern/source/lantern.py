"""Street-facing roof lantern of the former Taichang furniture company."""
from math import cos,sin,pi

def swatch(rgb):
    c=[x/255 for x in rgb]
    return dict(color=[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in c],roughness=.85,metallic=0)
PALETTE={n:swatch(c)for n,c in [('dark dome',(116,105,87)),('sloping cap',(129,118,99)),('pale pier',(148,133,109)),
    ('plain base',(142,127,108)),('relief bevel',(156,140,117)),('cornice lip',(165,147,120)),
    ('shaded joint',(110,99,85)),('upper bed',(147,128,105))]}

def shell(b,name,rings,sides,mat,phase=0):
    verts=[(r*sin(2*pi*j/sides+phase),-r*cos(2*pi*j/sides+phase),z)for z,r in rings for j in range(sides)]
    faces=[]
    for i in range(len(rings)-1):
        for j in range(sides):
            k=(j+1)%sides;faces.append((i*sides+j,i*sides+k,(i+1)*sides+k,(i+1)*sides+j))
    faces.extend([tuple(reversed(range(sides))),tuple(range((len(rings)-1)*sides,len(rings)*sides))])
    b.add(verts,faces,mat,name)

def post(b,name,theta,profile,mat):
    v=[]
    for z,r,w in profile:
        for dx,dy in [(-w,-w),(w,-w),(w,w),(-w,w)]:
            v.append(((r+dy)*sin(theta)+dx*cos(theta),-(r+dy)*cos(theta)+dx*sin(theta),z))
    faces=[(3,2,1,0)]
    for i in range(len(profile)-1):
        for j in range(4):faces.append((4*i+j,4*i+(j+1)%4,4*(i+1)+(j+1)%4,4*(i+1)+j))
    faces.append(tuple(range(len(v)-4,len(v))))
    b.add(v,faces,mat,name)

def add_building(b,lod=False):
    for i,(z0,z1,r0,r1,mat) in enumerate([
        (0,.11,1.15,1.15,'plain base'),(.11,.28,1.15,1.12,'plain base'),(.28,.56,1.12,.96,'sloping cap'),
        (.56,.605,.96,1.007,'relief bevel'),(.605,.646,1.007,1.007,'cornice lip'),
        (.646,.784,.969,.969,'plain base'),(.784,.818,.993,.993,'upper bed')]):
        shell(b,f'octagonal plinth section {i}',[(z0,r0),(z1,r1)],8,mat)
    # Visible panels on the inclined portion of the parapet are four shallow triangular planes.
    for j in [6,7,0,1]:
        a=2*pi*j/8+pi/8;front=(sin(a),-cos(a));along=(cos(a),sin(a));v=[]
        for x,z,r in [(-.27,.317,1.036),(.27,.317,1.036),(.215,.507,.953),(-.215,.507,.953),(0,.407,1.061)]:
            v.append((front[0]*r+along[0]*x,front[1]*r+along[1]*x,z))
        b.add(v,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],'relief bevel',f'faceted apron panel {j}')
    # The street-facing uprights are visible. The back is left open where the adjoining roof hides it.
    for j in [-2,-1,0,1,2]:
        a=j*pi/4
        post(b,f'pier plinth {j}',a,[(.815,.84,.113),(.852,.84,.113),(.881,.84,.083)],'upper bed')
        post(b,f'stone upright {j}',a,[(.878,.84,.080),(1.98,.84,.074)],'pale pier')
        post(b,f'spread capital {j}',a,[(1.977,.84,.074),(2.012,.84,.080),(2.064,.84,.112),(2.098,.84,.112)],'relief bevel')
    for i,(z0,z1,r0,r1,mat) in enumerate([
        (2.094,2.15,.96,.966,'upper bed'),(2.15,2.18,.966,1.021,'cornice lip'),(2.18,2.209,1.021,1.021,'upper bed'),
        (2.209,2.242,.978,.978,'shaded joint'),(2.242,2.287,.978,1.052,'cornice lip'),
        (2.287,2.327,1.052,1.052,'upper bed'),(2.327,2.345,1.006,1.006,'shaded joint'),
        (2.345,2.382,1.006,1.044,'cornice lip'),(2.382,2.411,1.044,1.044,'upper bed')]):
        shell(b,f'moulded polygonal eaves {i}',[(z0,r0),(z1,r1)],8,mat)
    shell(b,'round dome spring',[(2.405,.935),(2.425,.935)],24 if lod else 72,'shaded joint')
    rings=[]
    for i in range((7 if lod else 20)+1):
        a=(pi/2)*i/(7 if lod else 20)
        rings.append((2.422+.545*sin(a),max(.017,.925*cos(a))))
    shell(b,'shallow rounded dome',rings,28 if lod else 80,'dark dome')
    shell(b,'finial foot',[(2.962,.049),(2.976,.049),(2.992,.022)],12 if lod else 24,'upper bed')
