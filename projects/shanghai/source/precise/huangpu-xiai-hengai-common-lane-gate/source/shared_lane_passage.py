"""Stepped street lintel, open passage and the two guardroom windows of the shared gate."""
from functools import lru_cache
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Point,Polygon,box

from gatehouse_fabric import finish
from gatehouse_signs import PALETTE as SIGNS, add_gatehouse_signs

BEAM="Yongjia passage | dusty warm grey lintel"
SOFFIT="Yongjia passage | pale painted ceiling"
ARRIS="Yongjia passage | worn lintel arris"
WALL="Yongjia passage | guardroom lime render"
BASE="Yongjia passage | dark dado"
GROOVE="Yongjia passage | recessed dado joint"
SASH="Yongjia passage | brown guardroom joinery"
LIGHT="Yongjia passage | pale guardroom transom"
GLASS="Yongjia passage | shaded green guardroom glass"
GLASS2="Yongjia passage | pale reflected lower glass"
IRON="Yongjia passage | dark painted gate iron"
PAVE="Yongjia passage | shaded grey entrance paving"
RING="Yongjia passage | worn access ring"
LID="Yongjia passage | dark access cover"
PALETTE={**SIGNS,BEAM:finish((136,131,118),.95),SOFFIT:finish((155,149,132),.93),
         ARRIS:finish((120,118,108),.91),WALL:finish((163,157,142),.94),
         BASE:finish((95,95,89),.90),GROOVE:finish((77,80,74),.96),
         SASH:finish((72,62,53),.87),LIGHT:finish((152,150,129),.83),
         GLASS:finish((83,97,88),.38,.07),GLASS2:finish((116,130,118),.43,.06),
         IRON:finish((56,56,49),.68,.26),PAVE:finish((136,135,129),.93),
         RING:finish((152,150,138),.74,.36),LID:finish((86,87,80),.83,.32)}

@lru_cache(maxsize=1)
def readings():
    path=Path(__file__).resolve().parents[1]/"measurements/gatehouse-passage-readings.json"
    return json.loads(path.read_text())

def block(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],mat,label=label)

def head(b):
    # The eastern step has a diagonal foot. The shorter western steps lie
    # partly behind the service fittings in the December 2015 view.
    profile=[(-1.812,2.681),(-1.674,2.681),(-1.674,2.745),(-1.617,2.745),
             (-1.617,2.810),(-1.559,2.810),(-1.559,2.863),(-1.50,2.863),
             (-1.50,2.908),(-1.461,2.908),(-1.461,2.934),(1.304,2.934),
             (1.304,2.894),(1.381,2.894),(1.381,2.847),(1.463,2.847),
             (1.515,2.792),(1.554,2.792),(1.607,2.71),(1.812,2.71)]
    top=3.524
    field=Polygon(profile+[(profile[-1][0],top),(profile[0][0],top)])
    b.prism(field,-.453,.036,lambda x,z,d:(x,-d,z),BEAM,"Street lintel with different stepped ends")
    # Narrow section through the underside follows the exact stepped outer arris.
    band=field.intersection(Polygon(profile+[(x,z+.023) for x,z in reversed(profile)]).buffer(0))
    b.prism(band,-.456,.043,lambda x,z,d:(x,-d,z),ARRIS,"Stepped worn underside of street lintel")

def guardroom(b,depth,lod):
    west=-1.7315;info=readings()["guardroom"]
    bays=info["measured_bays_y_m"];sill=info["sill_z_m"];top=info["head_z_m"];bar=info["transom_z_m"]
    def side(shape,x0,x1,mat,label):
        b.prism(shape,x0,x1,lambda y,z,x:(x,y,z),mat,label)
    field=box(.43,0.,depth,2.965)
    holes=[box(start,sill,end,top) for start,end in bays]
    for hole in holes:field=field.difference(hole)
    side(field,west-.19,west,WALL,"Guardroom return with two actual window openings")
    # Seven narrow horizontal lines of the grey dado remain visible in the
    # 2017 shade. The window sills project in front of its top band.
    side(box(.44,.0,4.1,sill-.04),west,west+.022,GROOVE,"Guardroom lower joint bed")
    for i in range(7):
        z0=.015+i*.112;z1=min(z0+.103,sill-.041)
        side(box(.445,z0,4.097,z1),west+.019,west+.031,BASE,f"Guardroom dado course {i+1}")
    for i,(start,end) in enumerate(bays):
        label=f"Guardroom window {i+1}";mid=(start+end)/2
        outer=box(start,sill,end,top);opening=box(start+.049,sill+.054,end-.049,top-.052)
        side(outer.difference(opening),west-.092,west+.027,SASH,label+" deep outer frame")
        side(box(start-.024,sill-.057,end+.024,sill+.011),west-.069,west+.085,BASE,label+" projecting sill")
        side(box(start+.047,bar-.03,end-.047,bar+.032),west-.058,west+.004,SASH,label+" horizontal transom rail")
        side(box(mid-.024,sill+.045,mid+.024,top-.046),west-.061,west-.003,SASH,label+" central mullion")
        for j,(a,c) in enumerate([(start+.048,mid-.024),(mid+.024,end-.049)]):
            for k,(lo,hi) in enumerate([(sill+.054,bar-.030),(bar+.032,top-.052)]):
                light=box(a,lo,c,hi)
                side(light,west-.093,west-.083,LIGHT if k else [GLASS,GLASS2][(i+j)%2],label+f" inset {'transom' if k else 'lower pane'} {j+1}")
                if not lod:
                    side(light.difference(light.buffer(-.012,join_style=2)),west-.084,west-.047,SASH,label+f" timber glazing bead {j+1}.{k+1}")
    # The entry leaf folds against this return in the 2015 and 2017 open views.
    # It passes in front of the first window and leaves the lane centre clear.
    x=west+.102; a=.13;c=1.53
    for j,z in enumerate((.115,.795,1.162,2.431)):
        block(b,x-.017,x+.019,a,c,z-.018,z+.018,IRON,f"Retracted passage gate crossrail {j+1}")
    for j,y in enumerate(np.linspace(a+.018,c-.018,10)):
        w=.024 if j in (0,9) else .0115
        block(b,x-w,x+w,y-w,y+w,.051,2.468,IRON,f"Retracted passage gate upright {j+1:02d}")

def floor(b,depth,lod):
    cover=readings()["access_lid"];cx,cy=cover["fit_center_xy_m"];r=cover["fit_radius_m"]
    steps=12 if lod else 28
    rim=Point(cx,cy).buffer(r,quad_segs=steps);inner=Point(cx,cy).buffer(r-.026,quad_segs=steps)
    slab=box(-1.733,-.10,1.733,depth+.14)
    b.plan_prism(slab.difference(rim),-.078,0.,PAVE,"Walk-through passage floor with actual access opening")
    b.plan_prism(rim.difference(inner),-.043,.002,RING,"Worn circular entrance access ring")
    b.plan_prism(inner.buffer(-.003),-.018,.0002,LID,"Recessed plain access cover")
    block(b,-1.746,1.746,-.271,-.105,-.064,-.004,PAVE,"Stone threshold separating street and covered floor")

def add_passage(b,lod=False):
    data=readings()["passage"];depth=data["rear_y_m"];width=data["front_width_m"]
    head(b)
    block(b,-width/2-.12,width/2+.12,.447,depth,2.965,3.184,SOFFIT,"Covered entrance soffit ending over the lane")
    # Only the street-facing portion of the opposite reveal is visible.
    block(b,width/2,width/2+.19,.442,1.19,0,2.968,WALL,"Visible east return behind the street pier")
    guardroom(b,depth,lod)
    floor(b,depth,lod)
    add_gatehouse_signs(b,lod)
