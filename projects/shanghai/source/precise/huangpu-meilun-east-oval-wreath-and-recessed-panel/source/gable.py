"""Asymmetric street windows, recessed spandrels and the oval cartouche of Meilun East."""
from pathlib import Path
from math import pi,cos,sin
import numpy as np
from shapely.geometry import Polygon,box,LineString
from profile_tools import BRICK as STONE,slab,cb,bricks_uv

EDGE='Stone moulding';DARK='Incised stone groove';FRAME='Dark metal frame';GLASS='Smoked window glass'
CART='Cartouche rim and scrolls';BOSS='Raised oval boss';LEAF='Foliage under the cartouche'
PALETTE={}
for title,rgb in [(STONE,(255,255,255)),(EDGE,(155,150,137)),(DARK,(101,100,91)),(FRAME,(63,67,63)),(GLASS,(65,81,80)),(CART,(153,144,129)),(BOSS,(165,156,141)),(LEAF,(139,132,117))]:
    PALETTE[title]=dict(color=[(v/255)**2.2 for v in rgb],roughness=.85)
PALETTE[STONE]['texture']=str(Path(__file__).with_name('finish.png'))
BAYS=[(-2.05,1.46),(1.54,.91)]
CZ=2.55
def oval(rx,rz,xc,zc,n):
    return Polygon([(xc+rx*cos(t),zc+rz*sin(t))for t in np.linspace(0,2*pi,n,endpoint=False)])
def bead(b,pts,width,y0,y1,material,name,n):
    area=LineString(pts).buffer(width,quad_segs=n,cap_style='round',join_style='round')
    slab(b,area,y0,y1,material,name)
def dome(b,parts,rings):
    vertices=[];faces=[]
    for j in range(rings):
        a0=(pi/2)*j/rings;a1=(pi/2)*(j+1)/rings
        for i in range(parts):
            t0=2*pi*i/parts;t1=2*pi*(i+1)/parts
            def xyz(a,t):return (.177*cos(a)*cos(t),-.118-.096*sin(a),CZ+.264*cos(a)*sin(t))
            points=[xyz(a0,t0),xyz(a0,t1),xyz(a1,t1),xyz(a1,t0)]
            start=len(vertices)
            vertices.extend(points)
            if j==rings-1:faces.append([start,start+1,start+2])
            else:faces.extend([[start,start+1,start+2],[start,start+2,start+3]])
    b.add(vertices,faces,BOSS,'Convex oval cartouche face')
def model(b,lod=False):
    n=24 if lod else 64
    extent=box(-3.64,0,2.61,3.18)
    for x,h in BAYS:extent=extent.difference(box(x-h,1.23,x+h,2.94))
    slab(b,extent,0,.30,STONE,'Stone facade around separate windows')
    for i,(x,h) in enumerate(BAYS):
        window=box(x-h,1.23,x+h,2.94)
        for j,(delta,front,w) in enumerate([(.012,-.068,.047),(-.041,-.030,.025),(-.073,.058,.035)]):
            outer=box(x-h-delta,1.23-delta,x+h+delta,2.94+delta)
            inner=outer.buffer(-w,join_style='mitre')
            slab(b,outer.difference(inner),front,.125,EDGE if j<2 else FRAME,'Stepped window reveal')
        slab(b,window,.193,.216,GLASS,'Recessed dark glazing')
        stiles=3 if i==0 else 1
        for j in range(stiles):
            px=x-h+(j+1)*2*h/(stiles+1)
            cb(b,px-.020,px+.020,.105,.177,1.30,2.88,FRAME,'Vertical metal sash stiles')
        cb(b,x-h+.07,x+h-.07,.091,.150,1.79,1.84,FRAME,'Crossrail of the dark window')
        # The broad spandrel has repeated deep flutes to either side of its small inset panel.
        panel=box(x-h,.12,x+h,1.105)
        slab(b,panel,-.076,0,EDGE,'Slightly raised rectangular spandrel')
        inside=panel.buffer(-.082,join_style='mitre')
        slab(b,inside,-.095,-.07,STONE,'Stone field inside spandrel')
        frame=(box(x-h+.11,.224,x+h-.11,1.0).difference(box(x-h+.146,.258,x+h-.146,.965)))
        slab(b,frame,-.127,-.085,EDGE,'Outer spandrel frame')
        half=.405 if i==0 else .46
        outer=box(x-half,.30,x+half,.91)
        slab(b,outer,-.113,-.086,DARK,'Shadow cut around central rectangle')
        slab(b,outer.buffer(-.028,join_style='mitre'),-.142,-.105,EDGE,'Central raised spandrel lip')
        slab(b,outer.buffer(-.083,join_style='mitre'),-.155,-.139,STONE,'Flat face within the panel lip')
        count=7 if i==0 else 2
        for sign in (-1,1):
            for off in np.linspace(half+.08,h-.18,count):
                px=x+off*sign
                recess=box(px-.013,.275,px+.013,.973)
                slab(b,recess,-.107,-.091,DARK,'Vertical groove at spandrel side')
    cb(b,-.455,.435,-.041,.28,0,3.16,STONE,'Tall stone pier carrying the oval')
    for z in (.50,1.06,1.62,2.05):
        cb(b,-.455,.435,-.045,-.040,z,z+.012,DARK,'Fine horizontal pier joint')
    for rx,rz,front,back,material in [(.274,.367,-.083,-.038,CART),(.246,.33,-.122,-.078,EDGE),(.205,.294,-.146,-.116,CART)]:
        ring=oval(rx,rz,0,CZ,n).difference(oval(rx-.026,rz-.026,0,CZ,n))
        slab(b,ring,front,back,material,'Concentric oval cartouche moulding')
    slab(b,oval(.198,.285,0,CZ,n),-.118,-.038,DARK,'Recess around the projecting oval face')
    dome(b,n,5 if lod else 10)
    # Volutes at the upper corners and sides are distinct from the foliage below.
    for xc,zc,scale,sign in [(-.20,CZ+.307,.074,-1),(.20,CZ+.307,.074,1),(-.229,CZ+.035,.041,-1),(.229,CZ+.035,.041,1)]:
        ts=np.linspace(0,1.80*pi,13 if lod else 27)
        vals=[(xc+sign*(scale*(1-.76*t/(1.8*pi)))*cos(t),zc+scale*(1-.76*t/(1.8*pi))*sin(t))for t in ts]
        bead(b,vals,.015,-.165,-.075,CART,'Carved scroll with turned-in end',2 if lod else 4)
    ts=np.linspace(-1,1,13 if lod else 27)
    bead(b,[(.23*t,CZ+.359-.046*(1-t*t))for t in ts],.019,-.143,-.07,CART,'Curved band above oval',3)
    for sign in (-1,1):
        for j in range(9):
            t=j/8.;xc=sign*(.038+.236*t);zc=CZ-.35+.123*t*t
            pts=[(xc-.034,zc-.014),(xc,zc+.028),(xc+.037,zc+.017),(xc+.021,zc-.02)]
            slab(b,Polygon(pts),-.118,-.065,LEAF,'Pointed leaves gathered under the oval')
    for lo,hi,depth in [(3.105,3.145,-.045),(3.145,3.19,-.102),(3.19,3.26,-.160)]:
        cb(b,-3.69,2.66,depth,.33,lo,hi,EDGE,'Projecting continuous top moulding')
    bricks_uv(b)
