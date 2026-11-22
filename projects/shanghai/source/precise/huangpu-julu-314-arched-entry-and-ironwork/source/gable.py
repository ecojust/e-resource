"""Grey arched garden entrance and two scrollwork leaves photographed at 314 Julu Road."""
from pathlib import Path
from math import pi,cos,sin
from shapely.geometry import Polygon
from profile_tools import BRICK as STUCCO, cb,slab,bricks_uv

IRON='Scrollwork and rectangular gate frames'
BACK='Weathered red gate lining'
TRIM='Shadowed grey pier cornices'
CAP='Light-grey raised pier tops'
PALETTE={}
for n,c in [(STUCCO,(255,255,255)),(IRON,(54,49,45)),(BACK,(135,60,58)),(TRIM,(148,143,132)),(CAP,(174,168,153))]:
    PALETTE[n]=dict(color=[(v/255)**2.2 for v in c],roughness=.88)
PALETTE[STUCCO]['texture']=str(Path(__file__).with_name('finish.png'))
HALF=1.22
SPRING=2.40

def arch_point(t,outer=False):
    return HALF*cos(t), (3.89+.50*sin(t)) if outer else SPRING+1.46*sin(t)

def arch_band(b,lod):
    steps=20 if lod else 38
    t=[pi*i/steps for i in range(steps+1)]
    inner=[arch_point(a) for a in t];outer=[arch_point(a,True) for a in t]
    slab(b,Polygon(inner+list(reversed(outer))),-.125,.255,STUCCO,'Segmental raised arch over open tympanum')
    lower=[(x,z-.072) for x,z in outer]
    slab(b,Polygon(lower+list(reversed(outer))),-.165,.282,TRIM,'Narrow outer arch moulding')

def layered_pier(b,x):
    for lo,hi,width,front,material,label in [(0,2.44,.53,-.14,STUCCO,'Square stucco entrance pier'),(2.416,2.49,.60,-.18,TRIM,'Lower square impost'),(2.485,2.535,.624,-.19,CAP,'Impost projecting fillet'),(2.53,3.857,.49,-.124,STUCCO,'Upper pier'),(3.85,3.92,.566,-.16,TRIM,'Upper cornice'),(3.92,3.974,.605,-.188,CAP,'Projecting upper coping'),(3.974,4.033,.438,-.117,TRIM,'Pier cap plinth'),(4.033,4.105,.353,-.085,CAP,'Raised crown')]:
        cb(b,x-width/2,x+width/2,front,.30,lo,hi,material,label)

def scroll_points(x,z,sx,sz,lod):
    # An S-shaped stem turns into a spiral at its end. The paired upper and lower
    # motifs share their ends, matching the diamonds visible on the dated gate leaves.
    values=[]
    for a,b,c,d in [((0,0),(.015,.19),(.35,.34),(.367,.56)),((.367,.56),(.388,.81),(.128,.826),(.147,.674)),((.147,.674),(.151,.607),(.245,.604),(.257,.680))]:
        steps=8 if lod else 16
        for i in range(steps):
            t=i/steps;s=1-t
            xx=s**3*a[0]+3*s*s*t*b[0]+3*s*t*t*c[0]+t**3*d[0]
            zz=s**3*a[1]+3*s*s*t*b[1]+3*s*t*t*c[1]+t**3*d[1]
            values.append((x+sx*xx,-.217,z+sz*zz))
    values.append((x+sx*.257,-.217,z+sz*.680))
    return values

def gate_leaf(b,x,lod):
    lo=x-.584;hi=x+.584
    cb(b,lo,hi,-.169,-.126,.087,2.284,BACK,'Red metal backing of gate leaf')
    for xx in [lo,hi]:cb(b,xx-.018,xx+.018,-.216,-.124,.056,2.319,IRON,'Stile of iron leaf')
    for zz in [.079,2.297]:cb(b,lo,hi,-.215,-.122,zz-.022,zz+.022,IRON,'Iron frame rail')
    for sx in (-1,1):
        for z,sz in [(.141,1),(1.98,-1)]:
            a=scroll_points(x,z,sx,sz,lod);b.tube(a,.011,IRON,sides=4 if lod else 6,label='Paired outward scroll')
        # The central pair crosses at the middle of each leaf, then curls back inward.
        a=scroll_points(x-.226*sx,.76,sx,1,lod)
        b.tube(a,.011,IRON,sides=4 if lod else 6,label='Crossing stem of central diamond')
        for z,sz in [(.82,-1),(1.575,1)]:
            a=scroll_points(x+.492*sx,z,-sx,sz,lod)
            b.tube(a,.010,IRON,sides=4 if lod else 6,label='Side return scroll')
    cb(b,x-.07,x+.07,-.24,-.17,1.112,1.16,IRON,'Horizontal fastener block')

def model(b,lod=False):
    for direction in [-1,1]:
        layered_pier(b,direction*(HALF+.252))
        gate_leaf(b,direction*.610,lod)
    arch_band(b,lod)
    bricks_uv(b)
