"""Build the six visible scroll blocks, scored corner pier and short window reveal."""
from pathlib import Path
from math import sin, cos, pi
import numpy as np
from shapely.geometry import box, LineString, Point, Polygon
from profile_tools import BRICK,cb,slab,bricks_uv

FIELD='Weathered plaster frieze'
RELIEF='Raised cream cartouche'
EDGE='Capping stone'
SHADOW='Recessed moulding'
SEAM='Course joint'
GLASS='Reflected upper pane'
SASH='Red timber sash'
PALETTE={}
for item,rgb in [(BRICK,(255,255,255)),(FIELD,(196,191,180)),(RELIEF,(224,220,207)),(EDGE,(210,207,194)),(SHADOW,(138,137,127)),(SEAM,(159,155,145)),(GLASS,(98,106,105)),(SASH,(116,68,53))]:
    PALETTE[item]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.91)
PALETTE[BRICK]['texture']=str(Path(__file__).with_name('finish.png'))
# Cornice varies by street face. Coordinates here precede the return rotations.
FACES=[(0,-.90,.90),(-1,-4.34,-.90),(1,.90,2.48)]
Z_PANEL=3.46

def panel_marks(b,cx,lod):
    cb(b,cx-.407,cx+.407,-.104,-.027,3.073,3.847,FIELD,'Rectangular relief ground')
    center=Point(cx,Z_PANEL)
    resolution=4 if lod else 9
    outer=center.buffer(.219,quad_segs=resolution)
    inner=center.buffer(.198,quad_segs=resolution)
    slab(b,outer.difference(inner),-.145,-.100,RELIEF,'Round moulding around plain central boss')
    slab(b,center.buffer(.184,quad_segs=resolution),-.115,-.101,EDGE,'Smooth round centre')
    for dx in [-1,1]:
        for dz in [-1,1]:
            knots=[(.393,.103),(.363,.092),(.326,.111),(.330,.164),(.343,.222),(.325,.267),(.272,.303),(.205,.296),(.174,.264),(.178,.231),(.209,.209),(.231,.221),(.232,.242)]
            if lod:knots=knots[::2]
            curve=LineString([(cx+dx*x,Z_PANEL+dz*z)for x,z in knots])
            slab(b,curve.buffer(.019,cap_style=1,join_style=1,quad_segs=1 if lod else 2),-.149,-.101,RELIEF,'Inward-turning corner scroll')
            blade=[(.035,.241),(.079,.281),(.112,.329),(.161,.346),(.206,.335),(.157,.373),(.103,.366),(.063,.331)]
            slab(b,Polygon([(cx+dx*x,Z_PANEL+dz*z)for x,z in blade]),-.142,-.101,RELIEF,'Small leaf above or below the central circle')
            cb(b,cx+dx*.339-.024,cx+dx*.339+.024,-.135,-.100,Z_PANEL+dz*.035-.014,Z_PANEL+dz*.035+.014,RELIEF,'Paired short bars between the scrolls')
    cb(b,cx-.35,cx+.35,-.132,-.1,3.085,3.105,RELIEF,'Raised bottom border of the square panel')

def rotate(b,offset,side):
    if not side:return
    pivot=side*.90
    t=side*37*pi/180
    for part in b.parts[offset:]:
        v=np.asarray(part['vertices'],float);x=v[:,0].copy()-pivot;y=v[:,1].copy()
        v[:,0]=pivot+x*cos(t)-y*sin(t);v[:,1]=x*sin(t)+y*cos(t)
        part['vertices']=v.tolist()

def assembly(b,side,l,r,lod):
    start=len(b.parts); span=box(l,0,r,4.0)
    if side:
        window=(l+.39,r-.36) if side==1 else (-2.71,-1.52)
        xl,xr=window
        span=span.difference(box(xl,0,xr,2.55))
        cb(b,xl,xr,.304,.337,.0,2.55,GLASS,'Partly shown upper glazing')
        for x in [xl+.038,(xl+xr)/2,xr-.038]:cb(b,x-.030,x+.030,.190,.30,0,2.55,SASH,'Recessed vertical sash member')
        for z in [1.21,2.25,2.51]:cb(b,xl,xr,.177,.271,z-.029,z+.029,SASH,'Timber head and transom')
        for x in [xl-.051,xr+.051]:cb(b,x-.056,x+.056,-.069,.35,0,2.59,EDGE,'Upper window reveal')
    slab(b,span,0,.42,BRICK,'Short scored corner pier and wall returns')
    if side==0:
        for z in [.23,.69,1.15,1.61,2.07,2.53]:
            cb(b,l,r,-.011,.008,z-.012,z+.012,SEAM,'Horizontal incised joint on stone corner')
    for z0,z1,y,mat,label in [(2.81,2.87,-.085,EDGE,'Lower projecting bead'),(2.87,2.96,-.162,SHADOW,'Undercut beneath scroll frieze'),(2.96,3.032,-.229,EDGE,'Broad base of frieze'),(3.032,3.07,-.16,FIELD,'Frieze lower setback'),(3.847,3.89,-.158,SHADOW,'Shadow beneath coping'),(3.89,4.023,-.223,EDGE,'Stone parapet coping')]:
        cb(b,l,r,y,.42,z0,z1,mat,label)
    if side==0:
        for cx in [-.433,.433]:panel_marks(b,cx,lod)
    elif side==-1:
        for j in range(4):panel_marks(b,r-.43-j*.86,lod)
    else:
        for xx in [l+.34,l+.85,r-.23]:
            wedge=Polygon([(xx-.091,2.79),(xx+.091,2.79),(xx+.091,2.91),(xx-.091,2.91)])
            slab(b,wedge,-.276,-.055,SHADOW,'Brackets in the shaded return')
    rotate(b,start,side)

def model(b,lod=False):
    for section in FACES:assembly(b,*section,lod)
    bricks_uv(b)
