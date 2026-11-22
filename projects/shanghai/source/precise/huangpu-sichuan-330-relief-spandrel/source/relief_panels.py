"""Paired square foliate reliefs between street windows at 330 Middle Sichuan Road."""
from math import sin,cos,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box,Polygon
from shapely.ops import unary_union

ID='huangpu-sichuan-330-relief-spandrel'
WALL='Light ashlar jointed surface';GROOVE='Horizontal joint';TRIM='Dressed pale reveal';BASE='Dark spandrel plate';BORDER='Raised moulding';FOL='Broad rounded foliate crest';SIDE='Shadow flank of relief';RIM='Soft light on worn crest';FRAME='Dark sash';PANE='Dark street reflection';SKY='Cool grey glass'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(WALL,[1,1,1],.96),(GROOVE,[.543,.544,.505],.94),(TRIM,[.693,.694,.650],.91),(BASE,[.181,.189,.186],.78),(BORDER,[.236,.247,.239],.73),(FOL,[.286,.290,.270],.76),(SIDE,[.196,.204,.197],.82),(RIM,[.313,.306,.278],.74),(FRAME,[.173,.175,.153],.71),(PANE,[.159,.199,.207],.37),(SKY,[.256,.299,.304],.36)]}
def texture():
    p=Path(__file__).with_name('plaster.png')
    if not p.exists():
        rng=np.random.default_rng(535);size=(624,504);v=np.asarray(Image.fromarray(rng.integers(0,255,(42,51),dtype='u1')).resize(size,Image.Resampling.BICUBIC),float)
        v=(v-128)*.031+rng.normal(0,1.6,size[::-1]);im=np.clip([181,182,172]+v[:,:,None],0,255).astype('u1')
        Image.fromarray(im).quantize(120).save(p)
    PALETTE[WALL]['texture']=str(p)
F=lambda x,z,d:(x,-d,z)
def slab(b,p,lo,hi,m,label):b.prism(p,lo,hi,F,m,label)
def rect(b,x0,x1,z0,z1,lo,hi,m,label):slab(b,box(x0,z0,x1,z1),lo,hi,m,label)
CS=(-1.26,1.26);Z=2.73;OFFSET=.459
def ring(b,x,z,half,th,depth,m,name):
    a=box(x-half,z-half,x+half,z+half);slab(b,a.difference(a.buffer(-th,join_style=2)),.286,depth,m,name)
def leaf(b,c,z,ang,offset,tip,bend,width,far,name):
    # The outline narrows to a tip. The folded centre projects ahead of both margins.
    u=np.array([cos(ang),sin(ang)]);v=np.array([-sin(ang),cos(ang)]);origin=np.array([c,z])+u*offset
    n=5 if far else 10;verts=[];faces=[]
    for i in range(n+1):
        s=i/n;pos=origin+u*(s*tip)+v*(bend*sin(s*pi*.82))
        tangent=u*tip+v*(bend*pi*.82*cos(s*pi*.82));normal=np.array([-tangent[1],tangent[0]])/np.linalg.norm(tangent)
        w=max(.0004,width*sin(pi*s)**.77)
        for side,depth in [(-1,.313),(0,.321+.027*sin(pi*s)),(1,.313)]:
            q=pos+normal*side*w;verts.append(F(q[0],q[1],depth))
    for i in range(n):
        j=3*i
        faces.extend([(j,j+3,j+4,j+1),(j+1,j+4,j+5,j+2)])
    # Local winding of (longitudinal, lateral) faces the street.
    b.add(verts,faces,FOL,name)
def curl(b,c,z,angle,far):
    # Four inward coiling branches around the centre, with smaller fan leaves.
    u=np.array([cos(angle),sin(angle)]);v=np.array([-u[1],u[0]])
    pts=[]
    for phase in np.linspace(0,1,13 if far else 27):
        r=.094*(1.-phase*.86);a=.90*pi+phase*1.75*pi
        p=np.array([c,z])+u*(.133+r*cos(a))+v*(.054+r*sin(a))
        pts.append(F(p[0],p[1],.324))
    b.tube(pts,.013 if far else .015,FOL,5 if far else 8,'Inward curl of the four-part foliate ornament')
    for ang,offset,reach,curve,width in [(angle+.24,.14,.183,.007,.027),(angle+.53,.155,.179,-.017,.021),(angle-.04,.155,.178,.013,.023)]:
        leaf(b,c,z,ang,offset,reach,curve,width,far,'Tapered folded leaf fanning into the corner')
def ornament(b,c,far):
    rect(b,c-.969,c+.969,2.097,3.355,.134,.272,BASE,'Broad continuous dark plate between two windows')
    for low,high,d in [(2.073,2.112,.306),(2.119,2.148,.291),(3.318,3.349,.294),(3.351,3.394,.330)]:
        rect(b,c-.986,c+.986,low,high,.246,d,BORDER,'Four moulded horizontal edges of the dark spandrel')
    for off in (-OFFSET,OFFSET):
        x=c+off
        rect(b,x-.383,x+.383,Z-.375,Z+.375,.263,.298,BASE,'Square recessed background of one foliate panel')
        ring(b,x,Z,.378,.026,.324,BORDER,'Outer raised square frame surrounding one panel')
        if not far:ring(b,x,Z,.341,.009,.314,SIDE,'Narrow interior bead at the square panel edge')
        for angle in (pi/4,3*pi/4,5*pi/4,7*pi/4):curl(b,x,Z,angle,far)
        pts=[(x+.047*cos(t),Z+.047*sin(t))for t in np.linspace(0,2*pi,14 if far else 26,endpoint=False)]
        slab(b,Polygon(pts),.293,.333,BORDER,'Central boss where the four branches meet')
def window(b,c,low,hi,far):
    w=.875;xs=np.linspace(c-w,c+w,4);zs=[low,hi-.397,hi]
    for i in range(3):
        for j in range(2):
            rect(b,xs[i]+.011,xs[i+1]-.011,zs[j]+.022,zs[j+1]-.017,-.184,-.150,PANE if (i+j)%3 else SKY,'Glazing beneath rectangular overlight')
    for x in xs:rect(b,x-.017,x+.017,low,hi,-.176,-.088,FRAME,'Three-light steel casement and vertical stiles')
    for z in zs:rect(b,c-w-.013,c+w+.013,z-.022,z+.022,-.18,-.087,FRAME,'Continuous transom or perimeter sash')
    if not far:
        for x in xs[1:3]:rect(b,x-.004,x+.004,low+.038,hi-.039,-.092,-.083,BORDER,'Slim visible wear edge of metal mullion')
def add_building(b,far=False):
    texture()
    holes=[box(c-.90,lo,c+.90,hi) for c in CS for lo,hi in ((.12,2.068),(3.399,5.13))]
    wall=box(-2.50,0,2.50,5.52).difference(unary_union(holes));slab(b,wall,-.255,0,WALL,'Two vertical street window bays in the ashlar-faced wall')
    for z in np.arange(.19,5.50,.248):slab(b,wall.intersection(box(-2.5,z,2.5,z+.010)),-.001,.002,GROOVE,'Continuous thin horizontal course joint across broad masonry pier')
    for c in CS:
        ornament(b,c,far)
        for lo,hi in ((.12,2.068),(3.399,5.13)):
            window(b,c,lo,hi,far)
            rect(b,c-.928,c+.928,lo-.040,lo-.008,-.09,.070,TRIM,'Pale dressing at the lower edge of window')
        rect(b,c-.976,c+.976,5.13,5.207,-.114,.079,TRIM,'Squared head of upper window')
    for z0,z1,d in [(5.285,5.358,.094),(5.361,5.398,.135),(5.413,5.457,.163),(5.46,5.52,.182)]:
        rect(b,-2.53,2.53,z0,z1,-.258,d,TRIM,'Stepped pale string course over the upper window line')
    for p in b.parts:
        if p['material']==WALL:p['texcoords']=[[(x+2.55)/5.10,(z+.015)/5.55]for x,y,z in p['vertices']]
