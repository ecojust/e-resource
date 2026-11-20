"""Recessed shuttered windows, tall attached columns and the entrance axis."""
import math
import numpy as np
from shapely.geometry import Polygon, box, LineString

BRICK='rubbed red brick'
FIELD='weathered brown brick'
STONE='pale carved granite'
BASE='grey granite'
SHUTTER='grey green painted shutters'
GLASS='smoke blue glass'
DARK='dark timber frames'
ROOF='slate roofing'
SEAM='slate batten and flashings'
GOLD='ochre door timber'
PALETTE={
    BRICK:{'color':[.49,.202,.124],'roughness':.83},FIELD:{'color':[.385,.292,.238],'roughness':.9},
    STONE:{'color':[.72,.675,.575],'roughness':.85},BASE:{'color':[.414,.407,.371],'roughness':.83},
    SHUTTER:{'color':[.51,.53,.48],'roughness':.78},GLASS:{'color':[.125,.17,.18],'roughness':.32,'metallic':.15},
    DARK:{'color':[.21,.21,.19],'roughness':.74},ROOF:{'color':[.218,.230,.224],'roughness':.88},
    SEAM:{'color':[.30,.31,.296],'roughness':.73},GOLD:{'color':[.392,.189,.101],'roughness':.71}}

def arched(x,z,w,h,rise,segments=12):
    half=w/2
    angles=np.linspace(0,math.pi,segments+1)
    return Polygon([(x-half,z),(x+half,z)]+[(x+half*math.cos(t),z+h-rise+rise*math.sin(t))for t in angles])

def panel(f,x,z,w,h,back,front,mat,label):
    f.box(x,z,w,h,front-back,(back+front)/2,mat,label)

def mould(f,q,depth,mat,label,excluded_base=None):
    ring=q.buffer(.12,quad_segs=2,join_style=2).difference(q)
    if excluded_base is not None:ring=ring.intersection(box(-50,excluded_base,50,30))
    f.prism(ring,.006,depth,mat,label)

def arch_window(f,x,z,w,h,lod,closed=True,central=False,label='window'):
    rise=w*.42 if central else min(.25,w*.19)
    q=arched(x,z,w,h,rise,4 if lod else 12)
    if lod:
        # At the map's distant scale keep every real opening, its depth, shutters and sill.
        f.prism(q,-.30,-.28,GLASS,label+'/glass')
        if closed:
            panel(f,x,z+(h-rise)/2,w-.075,h-rise-.050,-.26,-.211,SHUTTER,label+'/shutter leaves')
        panel(f,x,z+h/2,.051,h-.07,-.25,-.128,DARK,label+'/mullions')
        panel(f,x,z-.047,w+.19,.108,-.01,.177,BASE,label+'/sills')
        return q
    f.prism(q,-.31,-.285,GLASS,label+'/glass')
    surround=q.difference(q.buffer(-.055,quad_segs=2,join_style=2))
    f.prism(surround,-.30,-.13,DARK,label+'/frame')
    if closed:
        # Individually inset shutters stop below the arched head.
        height=h-rise-.07
        for side in (-1,1):
            xx=x+side*(w-.12)/4
            panel(f,xx,z+.035+height/2,(w-.15)/2,height,-.269,-.209,SHUTTER,label+'/shutter leaves')
            if not lod:
                for k in range(1,12):
                    panel(f,xx,z+.044+height*k/12,(w-.20)/2,.027,-.211,-.184,BASE,label+'/louvre shadows')
    panel(f,x,z+h/2,.045,h-.07,-.28,-.126,DARK,label+'/mullions')
    panel(f,x,z+h-rise-.08,w-.04,.054,-.27,-.125,DARK,label+'/transoms')
    if not closed:
        for k in (1,2):
            panel(f,x,z+(h-rise)*k/3,w-.06,.040,-.28,-.14,DARK,label+'/sash bars')
    mould(f,q,.122,BRICK,label+'/brick surrounds')
    panel(f,x,z-.047,w+.19,.108,-.01,.177,BASE,label+'/sills')
    return q

def column(f,x,lod):
    b=f.builder;center=f.point(x,0,.038)[:2];name=f.label+'/colonnade'
    # Ground pier striped with real granite bands. The two upper floors share one brick shaft.
    panel(f,x,2.65,.71,5.00,-.11,.228,BRICK,'striped pier')
    for z in (.60,1.37,2.14,2.91,3.68,4.45,5.00):
        panel(f,x,z,.76,.235,-.109,.252,STONE,'rustication')
    b.lathe(center,[(5.06,.52),(5.19,.52),(5.24,.44),(5.38,.47),(5.43,.47),
                    (5.47,.39),(10.0,.337),(13.88,.311),(13.99,.343),(14.05,.365),
                    (14.18,.350),(14.35,.412)],BRICK,12 if lod else 22,name+'/red shafts')
    b.lathe(center,[(5.04,.53),(5.13,.53),(5.18,.45)],STONE,12 if lod else 20,name+'/base')
    f.box(x,14.51,.92,.19,.69,.1,STONE,'capital abacus')
    if lod:
        return
    # The two scrolling corners are separated by carved acanthus fans in the restoration detail.
    for side in (-1,1):
        r=.115;pts=[]
        for i,t in enumerate(np.linspace(0,math.tau,9 if lod else 14)):
            rad=r*(1-.5*t/math.tau)
            pts.append(f.point(x+side*(.275+rad*math.cos(t)),14.35+rad*math.sin(t),.32))
        b.tube(pts,.035,STONE,5 if lod else 7,name+'/volutes')
    for k in (-1,0,1):
        u=k*.14
        pts=[f.point(x+u*.25,14.01,.32),f.point(x+u-.06,14.22,.33),
             f.point(x+u,14.25,.405),f.point(x+u+.06,14.22,.33),f.point(x+u,14.39,.34)]
        b.add(pts,[(0,2,1),(0,3,2),(1,2,4),(2,3,4)],STONE,name+'/acanthus')

def central_axis(f,lod):
    holes=[]
    q=arched(0,.13,1.80,3.88,.90);holes.append(q)
    f.prism(q,-.84,-.81,DARK,'recessed entrance')
    for sign in (-1,1):
        panel(f,sign*.438,1.52,.86,2.75,-.81,-.73,GOLD,'entrance door leaves')
        panel(f,sign*.438,2.22,.66,.92,-.731,-.70,GLASS,'entrance lights')
    mould(f,q,.21,BRICK,'entrance archivolt',.11)
    ring=q.buffer(.30,quad_segs=3).difference(q.buffer(.235,quad_segs=3)).intersection(box(-2,.12,2,5))
    f.prism(ring,.01,.16,BRICK,'recessed arch bands')
    panel(f,0,4.10,.33,.30,.06,.233,STONE,'keystone')
    # Square entablature to middle tall casement and full round arch to the upper opening.
    holes.append(arch_window(f,0,5.61,2.0,3.65,lod,True,False,'central first floor'))
    ped=Polygon([(-1.33,9.60),(0,10.04),(1.33,9.60),(1.33,9.47),(-1.33,9.47)])
    f.prism(ped,.014,.195,BRICK,'central hood')
    holes.append(arch_window(f,0,10.49,2.06,3.70,lod,True,True,'central second floor'))
    return holes
