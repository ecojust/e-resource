"""Eight window openings and five small canopies on the photographed end wall of Zhengjia Lane."""
from functools import lru_cache
import json
import math
from pathlib import Path

import numpy as np

from courtyard_photo_plane import on_end,pixel

ROOT=Path(__file__).resolve().parents[1]
PICKS=json.loads((ROOT/"measurements/courtyard-window-picks.json").read_text())
WOOD="Zhengjia | dark stained shutter frames"
SLAT="Zhengjia | weathered shutter blades"
GLASS="Zhengjia | blue reflected glazing"
FRAME="Zhengjia | painted glazing bars"
GRILLE="Zhengjia | pale metal grille"
BLIND="Zhengjia | muted horizontal blind"
STONE="Zhengjia | grey projecting sill"
TILE="Zhengjia | faded red canopy panels"
EDGE="Zhengjia | aged dark canopy edge"
BRACKET="Zhengjia | canopy support brackets"
BOARD="Zhengjia | dark vertical boarding"
RECESS="Zhengjia | shade beyond shutters"

def paint(c,rough,metal=0.):
    v=np.array(c)/255.
    return {"color":np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),"roughness":rough,"metallic":metal}

PALETTE={WOOD:paint((48,39,38),.70),SLAT:paint((53,44,44),.76),GLASS:paint((66,91,129),.26,.23),
         FRAME:paint((48,43,46),.58),GRILLE:paint((137,137,128),.58,.22),BLIND:paint((88,94,101),.54,.12),
         STONE:paint((145,141,131),.79),TILE:paint((136,88,79),.75),EDGE:paint((69,59,52),.69),
         BRACKET:paint((99,82,62),.76),BOARD:paint((49,39,32),.83),RECESS:paint((32,30,31),.96)}

@lru_cache(maxsize=1)
def openings():
    rows=[]
    for obs in PICKS["rows"]:
        pts={k:on_end(*uv) for k,uv in obs["corners"].items()}
        rows.append({**obs,"left":(pts["TL"][0]+pts["BL"][0])/2,"right":(pts["TR"][0]+pts["BR"][0])/2,
                     "top":(pts["TL"][2]+pts["TR"][2])/2,"bottom":(pts["BL"][2]+pts["BR"][2])/2})
    return tuple(rows)

def block(b,l,r,y0,y1,bottom,top,mat,name):
    b.box(((l+r)/2,(y0+y1)/2,(bottom+top)/2),(r-l,y1-y0,top-bottom),mat,label=name)

def leaf_placement(row,index):
    l,r,base,head=[row[k] for k in ("left","right","bottom","top")]
    width=(r-l-.042)/2;sign=1 if index==0 else -1
    hinge=np.array([l+.019 if index==0 else r-.019,.040,(head+base)/2])
    if row["observed"][index]=="open":
        u=PICKS["swing_outer_edges_at_midheight"][row["key"]][index][0]
        def tip_pixel(angle):
            a=math.radians(angle)
            tip=hinge+width*np.array([sign*math.cos(a),-math.sin(a),0.])
            return pixel(tip)[0]
        # Only the visible outward branch is used. Projection of each free edge is monotone here.
        lo,hi=65.,165.
        increasing=tip_pixel(hi)>tip_pixel(lo)
        for _ in range(35):
            angle=(lo+hi)/2
            if (tip_pixel(angle)<u)==increasing:
                lo=angle
            else:
                hi=angle
        angle=(lo+hi)/2
    else:angle=0.
    a=math.radians(angle)
    return hinge,np.array([sign*math.cos(a),-math.sin(a),0.]),np.array([sign*math.sin(a),math.cos(a),0.]),width,angle

def leaf(builder,row,index,lod):
    h,d,n,width,angle=leaf_placement(row,index);h=h.copy();h[2]=0.
    bot,top=row["bottom"]+.029,row["top"]-.029
    thick=.036;z=np.array([0.,0.,1.]);tag=f"{row['key']} shutter {index+1} | "
    def box(s0,s1,t0,t1,a,b,mat,name):
        c=h+d*((s0+s1)/2)+n*((t0+t1)/2)+z*((a+b)/2)
        builder.box(c,(s1-s0,t1-t0,b-a),mat,basis=[d,n,z],label=tag+name)
    for s in [0.,width-thick]:box(s,s+thick,-.015,.020,bot,top,WOOD,"stile")
    box(thick,width-thick,-.015,.020,bot,bot+.072,WOOD,"bottom rail")
    box(thick,width-thick,-.015,.020,top-.054,top,WOOD,"top rail")
    floor,head=bot+.072,top-.054
    count=row["slat_count"]
    spacing=(head-floor)/count
    for j in range(count):
        # A bright opening in the lower middle of the photographed right shutter marks a displaced slat.
        broken=row["key"]=="upper-right" and index==1 and j==7
        tilt=math.radians(6 if broken else 34)
        delta=spacing*.22 if broken else 0.
        center=h+d*width/2+z*(floor+(j+.5)*spacing+delta)
        fore=n*math.cos(tilt)-z*math.sin(tilt)
        up=n*math.sin(tilt)+z*math.cos(tilt)
        builder.box(center,(width-2*thick,.008,spacing*.98),SLAT,basis=[d,fore,up],label=tag+f"inclined blade {j+1}")
    if not lod:
        for s in (thick-.006,width-thick+.006):
            box(s-.004,s+.004,-.018,-.015,bot+.033,top-.033,WOOD,"narrow stile molding")

def ordinary_opening(b,row,lod):
    l,r,bot,top=[row[k] for k in ("left","right","bottom","top")];tag=row["key"]+" | "
    for x in (l,r-.024):
        block(b,x,x+.024,.054,.14,bot,top,FRAME,tag+"reveal jamb")
    block(b,l+.024,r-.024,.054,.14,top-.030,top,FRAME,tag+"reveal head")
    block(b,l-.035,r+.041,-.096,.1,bot-.063,bot+.003,STONE,tag+"sill")
    if row["observed"][0]=="grille":
        pts=PICKS["ground_grille_x"]
        for i,uv in enumerate(pts):
            x=on_end(*uv,.025)[0]
            block(b,x-.007,x+.007,.025,.041,bot+.010,top-.010,GRILLE,tag+f"upright {i+1}")
        for i,uv in enumerate(PICKS["ground_grille_rails"]):
            zz=on_end(*uv,.018)[2]
            block(b,l+.020,r-.020,.014,.025,zz-.011,zz+.011,GRILLE,tag+f"tie rail {i+1}")
        for i in range(row["slat_count"]):
            step=(top-bot-.05)/row["slat_count"];zz=bot+.025+(i+.5)*step
            a=math.radians(23);basis=[[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]]
            b.box(((l+r)/2,.099,zz),(r-l-.052,.005,step*.96),BLIND,basis=basis,label=tag+f"blind strip {i+1}")
    elif row["observed"][0]=="board":
        for i in range(8):
            x=l+.016+i*(r-l-.032)/8
            block(b,x,x+(r-l-.032)/8-.002,.050,.085,bot+.012,top-.012,BOARD,tag+f"vertical board {i+1}")
    else:
        for i,condition in enumerate(row["observed"]):
            if condition=="open":
                width=(r-l)/2
                left=l+i*width+.023;right=l+(i+1)*width-.023
                block(b,left,right,.127,.137,bot+.025,top-.034,GLASS,tag+f"blue glazing {i+1}")
                for j in (1,2):
                    zz=bot+(top-bot)*j/3
                    block(b,left,right,.108,.127,zz-.012,zz+.012,FRAME,tag+f"cross bar {i+1}-{j}")
                for x in (left,right-.019):
                    block(b,x,x+.019,.106,.127,bot+.023,top-.029,FRAME,tag+"glazing stile")
            leaf(b,row,i,lod)
    block(b,l+.008,r-.008,.175,.193,bot+.005,top-.005,RECESS,tag+"unlit backing")

def canopy(b,row,lod):
    tag=row["key"]+" canopy | "
    e=PICKS["rooflet_corners"][row["key"]]
    u=on_end(*e["back_left"]);v=on_end(*e["back_right"])
    l,r=u[0],v[0];back=(u[2]+v[2])/2
    # Eaves are most visible in the two lower bays. Their rear edge is pinned to the photographed wall.
    projection=.36 if row["key"].startswith("middle") else .405
    front_points=[on_end(*e[k],-projection) for k in ("lip_left","lip_right")]
    front=min(back-.035,max(back-.125,sum(x[2] for x in front_points)/2))
    angle=math.atan2(back-front,projection)
    outward=np.array([0,math.cos(angle),math.sin(angle)])
    normal=np.array([0,-math.sin(angle),math.cos(angle)])
    count=4 if lod else 8
    for i in range(count):
        width=(r-l)/count
        b.box((l+(i+.5)*width,-projection/2,(back+front)/2),(width-.002,math.hypot(projection,back-front),.021),
              TILE,basis=[[1,0,0],outward,normal],label=tag+f"weathering panel {i+1}")
    block(b,l-.009,r+.009,-projection-.013,-projection+.014,front-.032,front+.006,EDGE,tag+"eave lip")
    block(b,l,r,-.015,.010,back-.020,back+.034,EDGE,tag+"back flashing")
    for x in (l+.072,r-.072):
        block(b,x-.015,x+.015,-.023,.008,front-.18,back,BRACKET,tag+"wall fixing")
        lo=np.array([x,-.023,front-.168]);hi=np.array([x,-projection*.79,front-.015]);d=hi-lo
        d=d/np.linalg.norm(d);n=np.array([0.,-d[2],d[1]])
        b.box((lo+hi)/2,(.024,np.linalg.norm(hi-lo),.022),BRACKET,basis=[[1,0,0],d,n],label=tag+"diagonal brace")

def add_windows(builder,lod=False):
    if lod in ("full","lod"):
        lod=lod=="lod"
    elif type(lod) is not bool:
        raise TypeError("Window detail level must be boolean, full, or lod")
    for row in openings():
        ordinary_opening(builder,row,lod)
        if row["key"] in PICKS["rooflet_corners"]:canopy(builder,row,lod)
