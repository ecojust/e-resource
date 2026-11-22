"""Two unlike adjacent stone window hoods at 117 Hongkong Road, as photographed in July 2015."""
from pathlib import Path
from math import pi,sin,cos
import numpy as np
from PIL import Image
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
ID='huangpu-hongkong-117-pedimented-windows'
WALL='Pale warm stucco';CAP='Cream stone cornice';LIGHT='Sunlit lip of the hood';SOFFIT='Recessed soffit';KEY='Wide projecting keystone';JOINT='Thin course joint';STEM='Stem between carved leaves';LEAF='Folded leaves in the jamb strip';PANE='Muted blue-grey glass';DARK='Dark bronze-coloured window frame';GRILLE='Pale steel window grille';GH='Dark glass reflection'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [(WALL,[1.,1.,1.],.95),(CAP,[.696,.679,.616],.91),(LIGHT,[.745,.727,.657],.91),(SOFFIT,[.544,.541,.502],.93),(KEY,[.682,.673,.612],.92),(JOINT,[.476,.467,.427],.96),(STEM,[.556,.554,.509],.93),(LEAF,[.660,.659,.596],.90),(PANE,[.308,.403,.399],.37),(GH,[.191,.258,.279],.40),(DARK,[.146,.153,.146],.68),(GRILLE,[.611,.632,.638],.63)]}
def texture():
    p=Path(__file__).with_name('plaster.png')
    if not p.exists():
        gen=np.random.default_rng(539);sz=(536,513)
        grain=np.asarray(Image.fromarray(gen.integers(0,255,(45,60),dtype='u1')).resize(sz,Image.Resampling.BICUBIC),float)
        v=(grain-128)*.046+gen.normal(0,1.9,sz[::-1]);Image.fromarray(np.clip([178,176,160]+v[:,:,None],0,255).astype('u1')).quantize(128).save(p)
    PALETTE[WALL]['texture']=str(p)
F=lambda x,z,d:(x,-d,z)
def slab(b,g,low,high,m,name):b.prism(g,low,high,F,m,name)
def rect(b,l,r,lo,hi,d0,d1,m,name):slab(b,box(l,lo,r,hi),d0,d1,m,name)
CS=(-1.255,1.255)
def leaf(b,x,z,side,far):
    pts=[];faces=[];n=4 if far else 9
    for i in range(n+1):
        q=i/n;cx=x+side*(.015+.103*sin(q*pi*.59));cy=z+.123*q+.048*sin(pi*q)
        hw=max(.001,.034*sin(pi*q)**.74)
        pts.extend([F(cx-side*hw,cy,.079),F(cx,cy,.080+.041*sin(pi*q)),F(cx+side*hw,cy,.079)])
    for i in range(n):
        j=i*3
        for face in ((j,j+1,j+4,j+3),(j+1,j+2,j+5,j+4)):
            faces.append(face if side>0 else tuple(reversed(face)))
    b.add(pts,faces,LEAF,'Folded paired blade on narrow vertical carved strip')
def windows(b,c,lo,hi,guard=False):
    w=.794
    for k,(z0,z1)in enumerate([(lo+.02,hi-.377),(hi-.338,hi-.017)]):
        for j in range(2):
            l=c-w+j*w+.022;r=l+w-.039
            rect(b,l,r,z0,z1,-.205,-.167,PANE if (j+k)%2 else GH,'Glazing in double-leaf dark window and overlight')
    for x in (c-w,c,c+w):rect(b,x-.021,x+.021,lo,hi,-.181,-.089,DARK,'Dark vertical shaft of the existing window')
    for z in (lo+.009,hi-.355,hi-.009):rect(b,c-w,c+w,z-.021,z+.021,-.185,-.085,DARK,'Dark window rail')
    if guard:
        xs=np.linspace(c-w+.047,c+w-.047,12)
        for x in xs:rect(b,x-.008,x+.008,lo+.023,hi-.018,-.026,-.007,GRILLE,'Fine pale vertical security grille of upper-left window')
        for j,x in enumerate(xs[:-1]):
            z=lo+(.398 if j%2 else .750)
            rect(b,x,xs[j+1],z-.009,z+.009,-.022,-.005,GRILLE,'Short staggered tie of the upper grille')
def hood(b,c,pointed,far):
    for side in (-1,1):
        x=c+side*.839
        rect(b,x-.042,x+.042,.055,2.082,-.04,.103,CAP,'Side dressing below the hood')
        rect(b,x-.082,x+.082,1.943,2.116,-.027,.141,LIGHT,'Block supporting the hood return')
    if not pointed:
        for lo,hi,half,d,m in [(2.045,2.104,1.045,.210,SOFFIT),(2.108,2.163,.986,.231,CAP),(2.162,2.212,1.092,.296,SOFFIT),(2.211,2.263,1.132,.345,LIGHT),(2.263,2.303,1.122,.323,CAP)]:
            rect(b,c-half,c+half,lo,hi,-.085,d,m,'Stepped flat cornice with a projecting drip edge')
        stone=Polygon([(c-.108,2.182),(c+.109,2.182),(c+.128,2.125),(c+.130,1.960),(c-.121,1.959)])
        slab(b,stone,-.043,.324,KEY,'Small central faceted keystone under the level hood')
    else:
        w=1.116;base=2.147;peak=2.639
        g=Polygon([(c-w,base),(c,peak),(c+w,base)])
        slab(b,g,-.060,.176,CAP,'Plain triangular tympanum above the right-hand opening')
        for off,th,d,m in [(.00,.045,.268,SOFFIT),(.035,.045,.307,CAP),(.074,.035,.339,LIGHT)]:
            f=Polygon([(c-w-.015,base+off),(c,peak+off),(c+w+.015,base+off),(c+w+.015,base+off+th),(c,peak+off+th),(c-w-.015,base+off+th)])
            slab(b,f,-.004,d,m,'Raking two-sided cornice of the triangular pediment')
        for side in (-1,1):
            l,r=(c-1.120,c-.206) if side<0 else (c+.206,c+1.121)
            rect(b,l,r,2.039,2.102,-.018,.243,CAP,'Interrupted band at the bottom of the pediment')
            rect(b,l,r,2.102,2.157,-.022,.302,LIGHT,'Stepped horizontal return below the pointed cornice')
        block=Polygon([(c-.145,1.975),(c+.134,1.975),(c+.153,2.573),(c+.017,2.642),(c-.143,2.581)])
        slab(b,block,-.039,.328,KEY,'Tall continuous central keystone reaches the sloping head')
    if not far:
        for side in (-1,1):
            x=c+side*.812
            rect(b,x-.008,x+.008,.065,1.926,.101,.111,LIGHT,'Thin highlight on edge of the jamb moulding')
def add_building(b,far=False):
    texture()
    openings=[box(c-.808,lo,c+.808,hi)for c in CS for lo,hi in ((.059,1.944),(3.518,4.992))]
    field=box(-2.53,0,2.53,5.10).difference(unary_union(openings));slab(b,field,-.289,0,WALL,'Two parallel stacked window axes with alternating street hoods')
    for z in np.arange(.19,5.06,.397):
        slab(b,field.intersection(box(-2.53,z,2.53,z+.012)),-.002,.003,JOINT,'Fine continuous horizontal joint in the window piers')
    for i,c in enumerate(CS):
        hood(b,c,bool(i),far);windows(b,c,.059,1.944);windows(b,c,3.518,4.992,guard=i==0)
        rect(b,c-.881,c+.881,3.414,3.503,-.061,.150,CAP,'Flat sill below the upper window')
        rect(b,c-.906,c+.906,3.490,3.527,-.025,.180,LIGHT,'Narrow drip at the upper sill')
        if i==0:
            rect(b,c-.567,c+.567,2.552,3.292,-.021,.050,CAP,'Shallow rectangular field with a small diamond')
            q=Polygon([(c-.183,2.888),(c,2.994),(c+.183,2.888),(c,2.785)])
            # Recessed diamond mark is defined by an outer face and four bevelled edges.
            slab(b,q,.045,.072,SOFFIT,'Diamond badge with darker sloping edge')
            slab(b,q.buffer(-.029,join_style=2),.067,.085,LIGHT,'Small central face within the lozenge')
        for side in (-1,1):
            x=c+side*.904
            rect(b,x-.067,x+.067,2.377,3.534,-.051,.064,STEM,'Narrow upright strip with successive pairs of carved leaves')
            for z in (2.410,2.621,2.833,3.045,3.255):
                for k in (-1,1):leaf(b,x,z,k,far)
            for z in (2.362,3.490):rect(b,x-.098,x+.098,z,z+.044,-.008,.100,CAP,'End cap of carved strip')
    for x in (-2.45,-.02,2.45):
        for z in np.arange(.03,5.02,.397):rect(b,x-.075,x+.075,z,min(z+.370,5.10),-.003,.043,CAP,'Rusticated continuous pilaster edge')
    for p in b.parts:
        if p['material']==WALL:p['texcoords']=[[(x+2.55)/5.1,(z+.02)/5.16]for x,y,z in p['vertices']]
