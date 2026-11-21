"""Brick-and-timber general office on the former Jiangnan site in Huangpu."""
import json
import math
from pathlib import Path

from shapely.geometry import LineString, Polygon
from photo_architecture import Facade, opening

P = json.loads(Path(__file__).with_name('parameters.json').read_text())
WALL = 'pale rendered masonry'
PLINTH = 'grey rendered plinth'
TRIM = 'carved pale stone'
SASH = 'painted timber sash'
GLASS = 'grey reflective window glass'
WOOD = 'brown entrance joinery'
TILE = 'weathered terracotta tile'
TILE_EDGE = 'fired tile lips'
CAP = 'pale roof coping'
METAL = 'painted sheet metal'
PALETTE = {
    WALL: {'color': [.77,.755,.688], 'roughness': .85},
    PLINTH: {'color': [.455,.458,.411], 'roughness': .88},
    TRIM: {'color': [.697,.683,.596], 'roughness': .84},
    SASH: {'color': [.168,.177,.151], 'roughness': .65},
    GLASS: {'color': [.191,.238,.231], 'roughness': .28, 'metallic': .28},
    WOOD: {'color': [.275,.133,.088], 'roughness': .70},
    TILE: {'color': [.477,.204,.134], 'roughness': .88},
    TILE_EDGE: {'color': [.385,.151,.099], 'roughness': .91},
    CAP: {'color': [.606,.588,.503], 'roughness': .82},
    METAL: {'color': [.338,.354,.297], 'roughness': .60, 'metallic': .35},
}
L,IW,IE,R = (P[k] for k in ('west_x','inner_west_x','inner_east_x','east_x'))
S,C,NW,NE = (P[k] for k in ('south_y','courtyard_y','west_north_y','east_north_y'))
EAVE,RIDGE = P['eave_m'],P['ridge_m']
WALL_RING = [(L,S),(R,S),(R,NE),(IE,NE),(IE,C),(IW,C),(IW,NW),(L,NW)]
ELEVATIONS = ['Longhua Road elevation','East outer return','East north gable',
              'East courtyard wall','South courtyard wall','West courtyard wall',
              'West north gable','West outer return']


def doorway(facade, u, wide, with_porch, lod):
    """Recessed timber doors and transom beneath separate, open-sided canopies."""
    facade.box(u,1.56,wide-.03,2.94,.16,-.32,WOOD,'recessed entry door')
    facade.box(u,2.79,wide-.23,.40,.07,-.20,GLASS,'door transom')
    facade.box(u,1.36,.075,2.32,.105,-.19,SASH,'double door meeting stile')
    for side in (-1,1):
        if not lod:
            facade.box(u+side*wide*.24,1.65,wide*.32,1.30,.055,-.203,GLASS,'door upper lights')
            facade.box(u+side*.115,1.05,.055,.29,.10,-.10,METAL,'entrance pulls')
    if not with_porch:
        return
    for side in (-1,1):
        facade.box(u+side*1.95,1.81,.40,3.02,.48,1.83,WALL,'porch square piers')
        facade.box(u+side*1.95,.37,.52,.31,.57,1.83,TRIM,'porch pier plinth')
    facade.box(u,3.33,4.62,.29,2.63,1.10,WALL,'flat porch fascia')
    facade.box(u,3.51,4.76,.10,2.78,1.11,CAP,'projecting canopy cap')
    for i in range(3):
        facade.box(u,.10+i*.075,4.38,.20+i*.15,1.94-i*.32,1.27-i*.16,TRIM,'three stone treads')


def elevation(builder, index, lod):
    a,b = WALL_RING[index], WALL_RING[(index+1)%len(WALL_RING)]
    wall = Facade(builder,a,b,ELEVATIONS[index]); front = index==0
    pitch = P['main_window_pitch_m'] if front else 2.45
    count = max(3,round((wall.length-1.6)/pitch)); spacing=(wall.length-1.6)/count
    bays = [-wall.length/2+.8+spacing*(i+.5) for i in range(count)]
    doors = [(x-wall.center[0],3.12,True) for x in P['porch_x']] if front else []
    if front:
        doors.append((3.1-wall.center[0],2.21,False))
    holes=[]; windows=[]
    for upper in (False,True):
        lo,hi = (P['upper_sill_m'],P['upper_head_m']) if upper else (P['lower_sill_m'],P['ground_head_m'])
        for i,u in enumerate(bays):
            if not upper and any(abs(u-d)<w/2+.73 for d,w,_ in doors):
                continue
            width = 1.00 if front else .99
            hole=opening(u,lo,width,hi-lo)
            holes.append(hole); windows.append((hole,upper))
    for u,width,_ in doors:
        holes.append(opening(u,.08,width,3.12))
    wall.wall(.02,EAVE,holes,thickness=.35,material=WALL)
    for hole,upper in windows:
        label=('first floor' if upper else 'ground floor')+' window'
        wall.window(hole,1 if lod else 2,2 if lod else (3 if upper else 4),
                    frame=SASH,glass=GLASS,trim=False,label=label)
        if not lod and front:
            x0,_,x1,z1=hole.bounds
            wall.box((x0+x1)/2,z1+.065,x1-x0+.16,.11,.21,.015,TRIM,'shallow lintels')
    for u,width,porch in doors:
        doorway(wall,u,width,porch,lod)
    if front:
        cuts=sorted((u-width/2-.09,u+width/2+.09) for u,width,_ in doors)
        start=-wall.length/2
        for left,right in cuts+[(wall.length/2,wall.length/2)]:
            if left>start:
                wall.box((left+start)/2,.20,left-start,.38,.17,0,PLINTH,'rendered plinth')
            start=right
    else:
        wall.beam(.20,.38,.055,PLINTH,label='rendered plinth')
    wall.beam(EAVE-.16,.21,.18,TRIM,label='eaves cornice')
    if not lod and index not in (2,6):
        intervals=max(2,round(wall.length/13))
        piers=[(a+b)/2 for a,b in zip(bays,bays[1:])
               if all(abs((a+b)/2-d)>w/2+.35 for d,w,_ in doors)]
        for i in range(1,intervals):
            expected=-wall.length/2+wall.length*i/intervals
            u=min(piers,key=lambda position:abs(position-expected))
            wall.line((u,.36,.15),(u,EAVE-.25,.15),.058,METAL,8,'rainwater pipes')
    if index in (2,6):
        outline=Polygon([(-wall.length/2,EAVE-.015),(wall.length/2,EAVE-.015),(0,RIDGE-.03)])
        wall.prism(outline,-.34,0,WALL,'north gable infill')


def solid_roof_face(builder, xy, height, name, lod, along_x):
    plan=Polygon(xy)
    if not plan.exterior.is_ccw:
        xy=list(reversed(xy))
    n=len(xy); top=[(x,y,height(x,y))for x,y in xy]
    verts=top+[(x,y,z-.16)for x,y,z in top]
    builder.add(verts,[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[
        (j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)],TILE,name+'/tiled roof plane')
    x0,y0,x1,y1=plan.bounds
    u0,u1=(y0,y1) if along_x else (x0,x1)
    nlines=max(2,round((u1-u0)/(.75 if lod else .38)))
    for i in range(1,nlines):
        u=u0+(u1-u0)*i/nlines
        line=LineString([(x0-1,u),(x1+1,u)] if along_x else [(u,y0-1),(u,y1+1)])
        clipped=plan.intersection(line)
        if clipped.is_empty or clipped.geom_type!='LineString' or clipped.length<.20:
            continue
        points=[(x,y,height(x,y)+.009) for x,y in clipped.coords]
        builder.tube(points,.024 if lod else .027,TILE_EDGE,4 if lod else 6,name+'/tile courses')


def roofs(builder,lod):
    # The two north ends are gabled. At the south corners the three ridges share hips and valleys.
    left,right=L-.30,R+.30; iw,ie=IW+.23,IE-.23
    south,court=S-.39,C+.28; west_north,east_north=NW+.31,NE+.31
    wr=(left+iw)/2;er=(right+ie)/2; ry=(south+court)/2
    a,b,c,d,e,f,g,h=((left,south),(right,south),(right,east_north),(ie,east_north),
                      (ie,court),(iw,court),(iw,west_north),(left,west_north))
    west,east=(wr,ry),(er,ry);wn,en=(wr,west_north),(er,east_north)
    faces=[([a,b,east,west],lambda x,y:(y-south)/(ry-south),True,'South road slope'),
           ([west,east,e,f],lambda x,y:(court-y)/(court-ry),True,'South court slope'),
           ([a,west,wn,h],lambda x,y:(x-left)/(wr-left),False,'West outer slope'),
           ([west,f,g,wn],lambda x,y:(iw-x)/(iw-wr),False,'West inner slope'),
           ([b,c,en,east],lambda x,y:(right-x)/(right-er),False,'East outer slope'),
           ([east,en,d,e],lambda x,y:(x-ie)/(er-ie),False,'East inner slope')]
    for vertices,gradient,along_x,name in faces:
        height=lambda x,y:EAVE+(RIDGE-EAVE)*gradient(x,y)
        solid_roof_face(builder,vertices,height,name,lod,along_x)
    for u,v in [(west,east),(west,wn),(east,en)]:
        builder.tube([(*u,RIDGE+.04),(*v,RIDGE+.04)],.115,TILE_EDGE,8,'Ridges/rounded crest tiles')
    for apex,lower in [(west,a),(east,b),(west,f),(east,e)]:
        builder.tube([(*lower,EAVE+.025),(*apex,RIDGE+.025)],.083,TILE_EDGE,8,'Ridges/hips and valleys')
    for x in (-23.,8.):
        builder.tube([(x,south,EAVE+.05),(x,ry,RIDGE+.10),(x,court,EAVE+.05)],.088,CAP,6,'Cross roof/raised copings')


def add_general_office(builder,lod=False):
    # A shallow continuous floor closes the historic envelope while keeping the north court open.
    builder.plan_prism(Polygon(WALL_RING),.013,.075,PLINTH,'Footprint/three connected wings')
    for edge in range(len(WALL_RING)):
        elevation(builder,edge,lod)
    roofs(builder,lod)
