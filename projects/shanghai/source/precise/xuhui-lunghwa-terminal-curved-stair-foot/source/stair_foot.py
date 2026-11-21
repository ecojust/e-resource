"""Six fan-shaped lower steps and the two stone newels of the old Lunghwa passenger hall."""
from math import sin, cos, pi
from pathlib import Path
from shapely.geometry import Polygon

TREAD = 'Warm veined stone'
NOSE = 'Rounded ivory nosing'
JOINT = 'Recessed stone joint'
CAP = 'Light chamfered cap'
BRASS = 'Polished brass tube'
CHEEK = 'Veined stone cheek'
BASE = 'Recessed plinth edge'
PALETTE = {
    TREAD: {'color': [1., 1., 1.], 'roughness': .43, 'texture': str(Path(__file__).with_name('pale-stone.png'))},
    NOSE: {'color': [.71,.577,.409], 'roughness': .49},
    JOINT: {'color': [.40,.329,.235], 'roughness': .84},
    CAP: {'color': [.78,.643,.497], 'roughness': .42},
    BRASS: {'color': [.76,.50,.187], 'metallic': .82, 'roughness': .25},
    CHEEK: {'color': [.71,.572,.425], 'roughness': .57},
    BASE: {'color': [.51,.408,.291], 'roughness': .64},
}
RISE=.154
GOING=.305
COUNT=6
LENGTH=COUNT*GOING
POST_X=2.43

def half_width(y):
    t=max(0.,min(1.,y/LENGTH))
    return 1.83+.47*(1.-t)**1.42

def textured(b,first):
    for part in b.parts[first:]:
        if part['material'] != TREAD:
            continue
        # Each slab samples a different part of the same original, non-photographic stone drawing.
        part['texcoords']=[[(x+2.8)/5.6,(.28+y*.47+z*.23)/1.9] for x,y,z in part['vertices']]

def prism(b,ring,z0,z1,material,name):
    first=len(b.parts)
    b.prism(Polygon(ring),z0,z1,lambda x,y,z:(x,y,z),material,name)
    textured(b,first)

def block(b,x,y,z,w,d,h,material,name):
    first=len(b.parts)
    b.box((x,y,z),(w,d,h),material,label=name)
    textured(b,first)

def closed_sections(b,rings,material,label):
    n=len(rings[0]);vertices=[p for ring in rings for p in ring]
    faces=[tuple(reversed(range(n))),tuple(range((len(rings)-1)*n,len(rings)*n))]
    for j in range(len(rings)-1):
        for i in range(n):
            nxt=(i+1)%n
            faces.append((j*n+i,j*n+nxt,(j+1)*n+nxt,(j+1)*n+i))
    b.add(vertices,faces,material,label)

def square_post(b,sign):
    label='Left' if sign<0 else 'Right'
    cx=sign*POST_X
    block(b,cx,0,.449,.299,.302,.898,TREAD,label+' limestone newel')
    # Sharp shadow line below a rounded slab, raised central stone on top.
    profile=[(.889,.155),(.896,.176),(.905,.19),(.926,.19),(.935,.179),(.94,.159)]
    for name,sections in [('lower cap',profile),('top cushion',[(.94,.15),(.956,.151),(.968,.141),(.974,.126)])]:
        rings=[[(cx+dx*r,dy*r,z)for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)]]for z,r in sections]
        closed_sections(b,rings,CAP,label+' newel '+name)

def add_stair(b,lod=False):
    # The front treads span between laterally flared cheek walls. The upper floor is beyond this measured portion.
    for i in range(COUNT):
        y=i*GOING;end=y+GOING;h=(i+1)*RISE;wf=half_width(y);wb=half_width(end);name=f'Tread {i+1}'
        outline=[(-wf,y), (wf,y), (wb,end), (-wb,end)]
        prism(b,outline,0,h-.044,JOINT,name+' backing')
        # Three broad stone slabs have visible narrow transverse joints. The leading arrises share a rounded profile.
        seams=([-.78,.73] if i%2==0 else [-1.07,.45])
        edgesf=[-wf,*seams,wf];edgesb=[-wb,*seams,wb]
        for j in range(3):
            a=edgesf[j]+(.002 if j else 0);c=edgesf[j+1]-(.002 if j!=2 else 0)
            aa=edgesb[j]+(.002 if j else 0);cc=edgesb[j+1]-(.002 if j!=2 else 0)
            prism(b,[(a,y+.008),(c,y+.008),(cc,end),(aa,end)],h-.05,h,TREAD,name+f' slab {j+1}')
            n=3 if lod else 8;profile=[(y+.012,h-.042)]
            for k in range(n+1):
                a0=-pi/2+pi*k/n
                profile.append((y-.008-.024*cos(a0),h-.022+.022*sin(a0)))
            profile.append((y+.012,h))
            ring=Polygon(profile)
            b.prism(ring,a,c,lambda yy,zz,xx:(xx,yy,zz),NOSE,name+f' rounded lip {j+1}')
        wall_depth=h-.043
        prism(b,[(-wf+.003,y-.001),(wf-.003,y-.001),(wf-.003,y+.008),(-wf+.003,y+.008)],max(0,h-RISE-.004),wall_depth,TREAD,name+' riser front')
    for sign in (-1,1):
        side='Left' if sign<0 else 'Right'
        square_post(b,sign)
        divisions=16 if lod else 44
        ys=[i*LENGTH/divisions for i in range(divisions+1)]
        for tag,zbase,top,w,mat in [('solid side',.0,.215,.145,CHEEK),('moulded ledge',.196,.245,.176,CAP)]:
            rings=[]
            for y in ys:
                cx=sign*(half_width(y)+.072)
                lo=0 if not zbase else zbase+y*RISE/GOING
                hi=top+y*RISE/GOING
                rings.append([(cx-w/2,y,lo),(cx-w/2,y,hi),(cx+w/2,y,hi),(cx+w/2,y,lo)])
            closed_sections(b,rings,mat,side+' '+tag)
        path=[(sign*(half_width(y)+.081),y,.904+y*RISE/GOING)for y in ys]
        # The tube enters the cap of the end post and follows the flare of the cheek. No intermediate post is visible in the six-step crop.
        path[0]=(sign*(POST_X-.06),0,.909)
        b.tube(path,.029,BRASS,sides=9 if lod else 20,label=side+' swept brass handrail')
