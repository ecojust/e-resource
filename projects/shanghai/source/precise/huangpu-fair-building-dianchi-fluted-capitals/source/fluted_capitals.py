"""Two adjoining fluted column heads with the cut frieze and projecting stonework above them."""
from math import sin,cos,pi

def stone(rgb):
    c=[v/255 for v in rgb]
    return dict(color=[x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in c],metallic=0,roughness=.82)

PALETTE={name:stone(rgb) for name,rgb in [
    ('limestone shaft',(177,171,156)),('column collar',(171,165,151)),('capital stone',(182,176,160)),
    ('square abacus',(180,173,156)),('architrave',(175,169,154)),('frieze face',(181,174,156)),
    ('cut channel',(154,147,133)),('cornice edge',(190,182,164)),('recessed bed',(156,149,135))]}

AXES=(-.89,.89)
FLUTES=20

def block(b,name,l,r,y0,y1,z0,z1,mat):
    vs=[(x,y,z) for z in (z0,z1) for x,y in ((l,y0),(r,y0),(r,y1),(l,y1))]
    b.add(vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,name)

def rings(b,name,x,profile,fluted,steps,mat):
    verts=[];faces=[];n=FLUTES*steps
    for height,r,cut in profile:
        for i in range(n):
            a=2*pi*i/n
            rr=r-(cut*sin(pi*(i%steps)/steps)**.75 if fluted else 0)
            verts.append((x+rr*sin(a),-rr*cos(a),height))
    for j in range(len(profile)-1):
        for i in range(n):
            k=(i+1)%n
            faces.append((j*n+i,j*n+k,(j+1)*n+k,(j+1)*n+i))
    faces.extend([tuple(reversed(range(n))),tuple(range(n*(len(profile)-1),n*len(profile)))])
    b.add(verts,faces,mat,name)

def add_building(b,lod=False):
    steps=3 if lod else 10
    for i,x in enumerate(AXES):
        rings(b,f'fluted stone shaft {i}',x,[(0,.274,.020),(.80,.268,.020),(.95,.266,.019)],True,steps,'limestone shaft')
        rings(b,f'grooved neck {i}',x,[(.95,.266,.019),(.966,.275,.017),(1.038,.275,.016),(1.063,.266,.001)],True,steps,'column collar')
        profile=[(1.06,.270,0),(1.069,.282,0),(1.083,.284,0),(1.094,.280,0),(1.11,.289,0),
                 (1.14,.307,0),(1.183,.331,0),(1.227,.354,0),(1.25,.362,0)]
        rings(b,f'rounded echinus {i}',x,profile,False,2 if lod else 5,'capital stone')
        block(b,f'square abacus {i}',x-.366,x+.366,-.365,.367,1.25,1.344,'square abacus')
    l,r=-1.281,1.281
    for j,(z0,z1,d,mat) in enumerate([(1.344,1.505,-.357,'architrave'),(1.505,1.518,-.376,'recessed bed'),
                                        (1.518,1.548,-.395,'architrave')]):
        block(b,f'architrave step {j}',l,r,d,.406,z0,z1,mat)
    block(b,'frieze backing behind channels',l,r,-.323,.405,1.548,1.81,'cut channel')
    runs=[];centreline=[-.89,0,.89]
    for centre in centreline:
        for dx in (-.072,0,.072):
            x=centre+dx;runs.append((x-.010,x+.010))
    start=l
    for i,(left,right) in enumerate(runs+[(r,r)]):
        block(b,f'frieze between cuts {i}',start,left,-.350,.39,1.548,1.81,'frieze face')
        start=right
    for j,(lo,hi,d,mat) in enumerate([(1.810,1.834,-.373,'frieze face'),(1.834,1.871,-.410,'cornice edge'),
        (1.871,1.893,-.397,'recessed bed'),(1.893,1.947,-.447,'architrave'),(1.947,2.025,-.486,'cornice edge'),
        (2.025,2.048,-.492,'cornice edge')]):
        block(b,f'projecting upper bed {j}',l-.015,r+.015,d,.428,lo,hi,mat)
