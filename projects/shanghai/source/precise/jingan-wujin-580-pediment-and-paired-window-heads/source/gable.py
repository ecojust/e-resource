"""Street-side shaped pediment and the first two adjacent segmental heads in the district photograph."""
from math import atan2,cos,sin,pi
from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from profile_tools import BRICK,cb,slab,bricks_uv
TILE='Brick arch and mouldings';STONE='Pale sloping coping';RECESS='Shade in a recessed brick panel';FRAME='Brown window frame';GLASS='Dull window glass';DARK='Shadow of a window reveal';MORTAR='Brick joint';PANEL='Burnt red triangular field'
col={BRICK:(255,255,255),TILE:(180,107,79),STONE:(170,159,144),RECESS:(120,68,58),FRAME:(112,83,70),GLASS:(76,85,88),DARK:(72,63,60),MORTAR:(128,92,78),PANEL:(145,73,57)}
PALETTE={m:{'color':[(v/255)**2.2 for v in rgb],'roughness':.88}for m,rgb in col.items()};PALETTE[BRICK]['texture']=str(Path(__file__).with_name('finish.png'))
GX=-1.82;L=GX-1.3;R=GX+1.3;WIN=[.40,2.14];S=1.33;RI=.78;ARCH_RISE=.50
def band(b,a,c,w,y0,y1,mat,name):
    dx=c[0]-a[0];dz=c[1]-a[1];length=(dx*dx+dz*dz)**.5;v=(-dz/length*w/2,dx/length*w/2)
    slab(b,Polygon([(a[0]+v[0],a[1]+v[1]),(c[0]+v[0],c[1]+v[1]),(c[0]-v[0],c[1]-v[1]),(a[0]-v[0],a[1]-v[1])]),y0,y1,mat,name)
def arc(cx,r,h,start,end,n):
    return [(cx+r*cos(start+(end-start)*j/n),S+h*sin(start+(end-start)*j/n))for j in range(n+1)]
def archhead(b,c,lod):
    # These are shallow semicircular panels above rectangular timber casements.
    poly=Polygon(arc(c,RI,ARCH_RISE,0,pi,20 if lod else 40));slab(b,poly,.065,.14,PANEL,'Recessed red window-head tympanum')
    number=13
    for j in range(number):
        a=j*pi/number+.008;e=(j+1)*pi/number-.008
        v=arc(c,RI+.135,ARCH_RISE+.14,a,e,1 if lod else 3)+arc(c,RI,ARCH_RISE,e,a,1 if lod else 3)
        slab(b,Polygon(v),-.056,.052,TILE,'Segmental ring individual voussoir')
    for outer in [False,True]:
        a=RI+.143 if outer else RI-.012;h=ARCH_RISE+.151 if outer else ARCH_RISE-.014
        breadth=.017
        tape=Polygon(arc(c,a,h,0,pi,18 if lod else 38)+arc(c,a-breadth,h-breadth,pi,0,18 if lod else 38))
        slab(b,tape,-.062,-.034,RECESS,'Recess line separating the segmental brick arch')
    cb(b,c-RI,c+RI,-.04,.09,S-.047,S+.014,FRAME,'Horizontal timber head')
    for x in [c-RI+.04,c,c+RI-.04]:cb(b,x-.029,x+.029,.105,.16,.10,S-.04,FRAME,'Part-visible vertical casement')
    for dx in [-.39,.39]:cb(b,c+dx-.334,c+dx+.334,.165,.194,.13,S-.066,GLASS,'Adjoining street sash glass')
    cb(b,c-RI,c+RI,.105,.165,.55,.602,FRAME,'Window horizontal muntin')
def model(b,lod=False):
    carrier=box(L,0,3.12,2.23);void=[]
    for c in WIN:
        head=arc(c,RI+.136,ARCH_RISE+.141,0,pi,28 if lod else 56)
        void.append(Polygon([(c-RI-.136,0),(c+RI+.136,0),*head]))
    slab(b,carrier.difference(unary_union(void)),.035,.52,BRICK,'Brick wall of adjacent pair')
    for c in WIN:archhead(b,c,lod)
    for x0,x1 in [(-.53,3.12)]:cb(b,x0,x1,-.038,.52,2.08,2.22,TILE,'Top band above the two segmental window heads')
    outline=Polygon([(L,0),(R,0),(R,4.35),(GX,5.17),(L,4.35)])
    outer=box(GX-.59,2.39,GX+.59,3.66);slab(b,outline.difference(outer),-.11,.64,BRICK,'Red brick upper end bay')
    cb(b,GX-.59,GX+.59,.085,.119,2.39,3.66,DARK,'Deep upper window opening')
    for side in [-1,1]:
        x=GX+side*.89
        cb(b,x-.095,x+.095,-.22,.12,2.20,4.17,TILE,'Narrow vertical pilaster')
        cb(b,x-.134,x+.134,-.251,.13,4.04,4.18,TILE,'Projecting pilaster capital')
        cb(b,x-.116,x+.116,-.238,.11,2.16,2.27,STONE,'Pilaster foot')
    cb(b,GX-.63,GX+.63,-.179,.10,3.64,3.76,TILE,'Square window head')
    cb(b,GX-.63,GX+.63,-.19,.13,2.34,2.43,STONE,'Pale upper window sill')
    for j in [-1,1]:
        x=GX+j*.34;cb(b,x-.196,x+.196,.055,.084,2.51,3.54,GLASS,'Original dark recessed glazing')
    for x in [GX-.527,GX,GX+.527]:cb(b,x-.031,x+.031,.009,.09,2.43,3.64,FRAME,'Vertical upper window framework')
    cb(b,GX-.55,GX+.55,.006,.095,2.86,2.907,FRAME,'Upper window horizontal bar')
    ped=Polygon([(L+.07,4.16),(R-.07,4.16),(GX,5.06)]);slab(b,ped,-.144,-.085,PANEL,'Triangular brick tympanum')
    for side in [-1,1]:
        e=(GX+side*1.27,4.30);peak=(GX,5.11)
        band(b,e,peak,.127,-.205,.53,TILE,'Moulded red-brick sloping verge')
        band(b,(e[0]+side*.025,e[1]+.079),(GX,5.201),.078,-.232,.57,STONE,'Narrow pale gable coping')
        band(b,(GX+side*1.04,4.31),(GX,4.969),.038,-.19,-.11,TILE,'Inner raised triangular edge')
    cb(b,L+.015,R-.015,-.205,.35,4.097,4.233,TILE,'Horizontal pediment bed')
    # At the base of this upper bay the picture shows the tip of a second, smaller pediment.
    for side in [-1,1]:band(b,(GX+side*.96,.964),(GX,1.66),.085,-.228,.12,STONE,'Visible tip of lower pediment moulding')
    bricks_uv(b)
