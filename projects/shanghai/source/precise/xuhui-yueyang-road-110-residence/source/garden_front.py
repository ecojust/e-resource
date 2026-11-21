"""Garden elevation with a recessed porch, projecting glazed room and stepped roofs."""
import math

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade

WALL = 'butter cream roughcast'
EDGE = 'warm limestone moulding'
WOOD = 'dark stained casement frames'
GLASS = 'shaded multi-light glass'
DOOR = 'dark mahogany door panels'
TILE = 'weathered vermilion pantiles'
TILE_LIGHT = 'faded orange tile courses'
STONE = 'red brown garden steps'
SOFFIT = 'cream rain canopy soffit'

PALETTE = {
    WALL: {'color': [.84, .790, .650], 'roughness': .92},
    EDGE: {'color': [.83, .805, .72], 'roughness': .81},
    WOOD: {'color': [.179, .122, .088], 'roughness': .67},
    GLASS: {'color': [.239, .267, .267], 'roughness': .26, 'metallic': .16},
    DOOR: {'color': [.245, .091, .052], 'roughness': .64},
    TILE: {'color': [.578, .180, .088], 'roughness': .84},
    TILE_LIGHT: {'color': [.674, .248, .122], 'roughness': .79},
    STONE: {'color': [.465, .180, .116], 'roughness': .87},
    SOFFIT: {'color': [.67, .634, .515], 'roughness': .88},
}


def casement(face, opening, panels, lights, height_lights, label):
    left, bottom, right, top = opening.bounds
    edge = opening.buffer(-.051, join_style=2)
    divisions = []
    pane_width = (right-left)/panels
    for i in range(1, panels):
        x = left+pane_width*i
        divisions.append(box(x-.049, bottom, x+.049, top))
    for i in range(panels):
        for j in range(1, lights):
            x = left+pane_width*(i+j/lights)
            divisions.append(box(x-.014, bottom, x+.014, top))
    for j in range(1, height_lights):
        z = bottom+(top-bottom)*j/height_lights
        divisions.append(box(left,z-.016,right,z+.016))
    panes = edge.difference(unary_union(divisions))
    face.prism(opening, -.190, -.169, GLASS, label+' glass')
    face.prism(opening.difference(panes), -.128, -.070, WOOD, label+' wood sash')
    face.box((left+right)/2, bottom-.055, right-left+.15, .11, .18, .025, EDGE, label+' sill')


def canopy(builder, left, right, front, rear, level, rafters):
    builder.plan_prism(box(left,front,right,rear), level, level+.13, SOFFIT, 'Porch and garden-facing canopy')
    builder.box(((left+right)/2,front,level+.12),(right-left+.05,.14,.165),EDGE,label='Canopy nose')
    for x in np.linspace(left+.20,right-.20,rafters):
        builder.box((x, front+.23, level-.061),(.11,.54,.152),EDGE,label='Exposed paired rafter end')


def south_roof(builder, left, right, front, depth, eave, rise, lod, label):
    """Model only the photographed near pitch. The ridgeline terminates the roof section."""
    inset=min(depth*.7,(right-left)*.32);rear=front+depth;ridge=eave+rise
    corners=[(left,front,eave),(right,front,eave),(right-inset,rear,ridge),(left+inset,rear,ridge)]
    builder.add(corners,[(0,1,2,3)],TILE,label+' visible front pitch')
    for x,side in ((left,0),(right,1)):
        a=corners[side];end=corners[3 if side==0 else 2]
        half=[a,end,(x,rear,eave)] if side==0 else [a,(x,rear,eave),end]
        builder.add(half,[(0,1,2)],TILE,label+' hip end')
        builder.tube([a,end],.066,TILE_LIGHT,7 if lod else 10,label+' diagonal ridge tiles')
    builder.box(((left+right)/2,front+.04,eave-.044),(right-left,.21,.12),EDGE,label='Deep projecting eaves')
    builder.tube([corners[3],corners[2]],.079,TILE_LIGHT,7 if lod else 12,label+' ridge')
    for i in range(1,10 if lod else 18):
        z=i/(10 if lod else 18)
        builder.tube([(left+inset*z,front+depth*z,eave+rise*z+.009),(right-inset*z,front+depth*z,eave+rise*z+.009)],.013 if lod else .018,TILE_LIGHT,4 if lod else 6,label+' tile lap')
    if not lod:
        for x in np.arange(left+.11,right-.04,.183):
            end=min((x-left)/inset,(right-x)/inset,1)
            if end>.035:builder.tube([(x,front,eave+.013),(x,front+end*depth,eave+end*rise+.013)],.031,TILE,6,label+' tapered clay pan')
    # Close the cut roof section where the available photographs stop.
    back=[(left,rear,eave-.055),(right,rear,eave-.055),corners[2],corners[3]]
    builder.add(back,[(0,3,2,1)],SOFFIT,label+' rear cut face')


def facade(builder,lod):
    room=Facade(builder,(-3.97,0),(4.20,0),'Projecting room')
    upper=box(-3.32,4.80,3.34,6.61)
    room.wall(4.08,7.11,[upper],.23,WALL)
    casement(room,upper,6,2,4,'Central wide garden window')
    builder.plan_prism(box(-4.13,-.13,4.35,1.82),3.92,4.10,WALL,'Garden-room floor and overhang')
    canopy(builder,-6.36,4.39,-.81,1.64,3.80,16)
    for x in (-3.82,4.04):
        builder.box((x,.33,2.17),(.40,.60,3.48),WALL,label='Porch square side pier')
        builder.box((x,.28,.58),(.52,.64,.27),EDGE,label='Porch pier plinth')
    porch=Facade(builder,(-4.04,1.69),(4.24,1.69),'Ground porch')
    doorway=box(-2.47,.55,2.47,3.20);porch.wall(.43,3.94,[doorway],.25,WALL)
    casement(porch,doorway,4,1,2,'Door and side lights')
    for x in (-.633,.633):
        porch.prism(box(x-.59,.59,x+.59,2.64),-.060,-.008,DOOR,'Two central garden door leaves')
        porch.prism(box(x-.46,.76,x+.46,2.42),-.011,.023,WOOD,'Garden door recessed panel')
    for i in range(4):
        builder.plan_prism(box(-2.91,-1.40+.29*i,2.86,1.72),.005+i*.134,.139+i*.134,STONE,'Four risers to the garden')
    for x in (-3.96,4.18):
        builder.plan_prism(box(x-.10,0,x+.10,2.35),4.06,7.13,WALL,'Garden-room side return')
    # Right-hand bay is partly screened by trees. Build the photographed window and first return.
    right=Facade(builder,(4.20,2.01),(9.66,2.01),'Recessed east wing')
    low=box(-2.31,.93,2.25,2.91);high=box(-2.31,4.83,2.11,6.56)
    right.wall(.39,7.07,[low,high],.25,WALL)
    casement(right,low,4,1,3,'East lower broad garden window')
    casement(right,high,3,1,3,'East upper garden window')
    right.box(0,3.92,right.length+.13,.18,.33,.04,EDGE,'Course between floors')
    left=Facade(builder,(-8.26,1.98),(-3.97,1.98),'Western balcony')
    opening=box(-1.52,1.02,1.52,3.14);door=box(-1.11,4.19,1.52,6.48)
    left.wall(.37,7.03,[opening,door],.25,WALL)
    casement(left,opening,3,1,3,'West garden casement')
    casement(left,door,2,1,3,'Balcony door')
    builder.plan_prism(box(-8.27,1.04,-3.97,2.26),3.91,4.10,WALL,'West balcony slab')
    for x in np.linspace(-8.14,-4.13,11):
        builder.box((x,1.09,4.45),(.106,.16,.71),EDGE,label='Pale square balcony baluster')
    builder.box((-6.13,1.09,4.85),(4.24,.23,.16),WALL,label='Balcony coping')
    for x in (-8.20,-4.04):
        builder.box((x,1.57,4.43),(.18,.98,.73),WALL,label='Balcony side upstand')
    for x,y in ((-8.27,1.98),(9.66,2.01)):
        builder.plan_prism(box(x-.11,y,x+.11,6.34),.34,7.06,WALL,'End of the documented elevation')
    for left_x,right_x,y in ((-8.29,-3.97,1.98),(4.20,9.70,2.01)):
        builder.plan_prism(box(left_x,y-.12,right_x,6.29),.08,.39,STONE,'Garden wing plinth')
    south_roof(builder,-8.63,-3.67,1.59,3.29,7.12,.97,lod,'Lower western hip')
    south_roof(builder,-4.31,4.48,-.36,4.05,7.13,1.63,lod,'Projecting central hip')
    south_roof(builder,4.21,10.16,1.59,3.79,7.11,1.73,lod,'Set-back eastern hip')
    for x,y,z in ((-1.29,3.36,8.32),(7.95,4.56,8.22)):
        builder.box((x,y,z+.43),(.35,.46,.87),WALL,label='Pale chimney seen above the garden roof')
        builder.box((x,y,z+.89),(.43,.53,.09),EDGE,label='Chimney crown')
