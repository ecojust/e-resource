"""Three photographed window axes at the street corner of the former Zhongxing Bank."""
from math import atan2, ceil, cos, sin
from pathlib import Path

import numpy as np
from shapely.geometry import box
from shapely.ops import unary_union

from stone import wall_uv

RADIUS = 9.733486353059083
HALF = 6.523359974253377
BAY = 2 * HALF / 3
AXES = (-BAY, 0., BAY)
HEIGHT = 21.66
FLOORS = (4.67, 8.13, 11.59, 15.05)
STONE = 'cream jointed facing'
BASE = 'warm ground stone'
PANEL = 'pale recessed panels'
GLASS = 'grey blue glazing'
FRAME = 'dark metal sash'
CORNICE = 'weathered pale moulding'
REAR = 'neutral cut surface'
PALETTE = {
    STONE: {'color':[1.,1.,1.], 'texture':str(Path(__file__).with_name('limestone.png')), 'roughness':.84},
    BASE: {'color':[.63,.56,.47], 'roughness':.83},
    PANEL: {'color':[.70,.70,.67], 'roughness':.88},
    GLASS: {'color':[.155,.218,.246], 'roughness':.29},
    FRAME: {'color':[.145,.15,.147], 'metallic':.28,'roughness':.54},
    CORNICE: {'color':[.66,.63,.56], 'roughness':.85},
    REAR: {'color':[.48,.46,.42], 'roughness':.9}
}

def point(s,z,d):
    angle = s / RADIUS
    return ((RADIUS+d)*sin(angle), RADIUS-(RADIUS+d)*cos(angle), z)

def prism(b,outline,back,front,material,name,spacing):
    """Sample the arc before triangulation so long faces follow the surveyed street curve."""
    if outline.is_empty:
        return
    left,bottom,right,top=outline.bounds
    n=max(1,ceil((right-left)/spacing))
    for a,c in zip(np.linspace(left,right,n+1)[:-1],np.linspace(left,right,n+1)[1:]):
        polygon=outline.intersection(box(a,bottom-.01,c,top+.01))
        if polygon.area>1e-8:
            b.prism(polygon,back,front,point,material,name)

def rectangle(b,left,bottom,right,top,back,front,material,name,spacing):
    prism(b,box(left,bottom,right,top),back,front,material,name,spacing)

def glass_and_sash(b,x,z,width,height,group,lod):
    span=.62 if lod else .38
    x0,x1=x-width/2,x+width/2
    rectangle(b,x0,z,x1,z+height,-.35,-.33,GLASS,group+' glass',span)
    for xx in (x0+.038,x1-.038):
        rectangle(b,xx-.038,z,xx+.038,z+height,-.26,-.18,FRAME,group+' outer frame',span)
    for zz in (z+.035,z+height-.035,z+height*.71):
        rectangle(b,x0,zz-.035,x1,zz+.035,-.26,-.17,FRAME,group+' transom',span)
    if group=='Ground floor':
        for xx in (x-width*.25,x,x+width*.25):
            rectangle(b,xx-.035,z,xx+.035,z+height,-.26,-.175,FRAME,'Ground vertical bars',span)
        if not lod:
            for zz in (z+height*.35,z+height*.53):
                rectangle(b,x0,zz-.022,x1,zz+.022,-.245,-.195,FRAME,'Ground crossbars',span)

def cladding_course(b,z,holes,material,lod):
    # Photograph shows shallow horizontal joints in the ground-storey facing.
    panel=box(-HALF,z,HALF,z+.024).difference(holes)
    prism(b,panel,.0005,.009,material,'Ground facing courses',.8 if lod else .43)

def add_building(b,lod):
    from repeat import repeat_only_texture
    repeat_only_texture(b,'limestone.png')
    step=.75 if lod else .40
    ground=[];upper=[];insets=[];top=[]
    for axis in AXES:
        ground.append(box(axis-1.13,.70,axis+1.13,3.40))
        glass_and_sash(b,axis,.70,2.26,2.70,'Ground floor',lod)
        for z in FLOORS:
            for dx in (-.68,.68):
                upper.append(box(axis+dx-.51,z,axis+dx+.51,z+1.94))
                glass_and_sash(b,axis+dx,z,1.02,1.94,'Upper paired window',lod)
            if z!=FLOORS[0]:
                inset=box(axis-1.29,z-1.14,axis+1.29,z-.37)
                insets.append(inset)
                prism(b,inset,-.27,-.105,PANEL,'Shallow rectangular spandrel',step)
                rectangle(b,axis-1.35,z-.37,axis+1.35,z-.29,-.095,.084,CORNICE,'Spandrel upper lip',step)
            rectangle(b,axis-1.27,z-.10,axis+1.27,z-.018,-.018,.078,CORNICE,'Paired window sill',step)
        for dx in (-.59,.59):
            top.append(box(axis+dx-.465,19.24,axis+dx+.465,20.58))
            glass_and_sash(b,axis+dx,19.24,.93,1.34,'Top band pair',lod)
    g=unary_union(ground)
    prism(b,box(-HALF,0,HALF,4.47).difference(g),-.5,0,BASE,'Ground storey street wall',step)
    for z in np.arange(.50,4.40,.50):
        cladding_course(b,z,g,CORNICE,lod)
    prism(b,box(-HALF,4.47,HALF,18.75).difference(unary_union(upper+insets)),-.47,0,STONE,'Punched curved wall',step)
    prism(b,box(-HALF,18.75,HALF,HEIGHT).difference(unary_union(top)),-.47,0,STONE,'Rounded top window band',step)
    for lo,hi,out,name in [(0,.16,.085,'Ground plinth'),(.16,.28,.045,'Plinth upper step'),
            (4.24,4.36,.16,'Ground cornice bed'),(4.36,4.48,.32,'Ground cornice cap'),
            (18.19,18.29,.12,'Eaves bed'),(18.29,18.40,.24,'Eaves lower step'),
            (18.40,18.52,.47,'Eaves middle step'),(18.52,18.66,.62,'Eaves upper slab'),
            (18.66,18.75,.52,'Eaves drip'),(21.51,HEIGHT,.10,'Thin parapet edge')]:
        rectangle(b,-HALF,lo,HALF,hi,-.08,out,CORNICE,name,step)
    for axis in AXES:
        for side in (-1,1):
            # Paired stepped brackets below the principal cornice.
            for offset in (-.074,.074):
                x=axis+side*1.60+offset
                for lo,hi,projection in [(17.69,17.83,.115),(17.83,17.97,.21),(17.97,18.12,.32),(18.12,18.35,.44)]:
                    rectangle(b,x-.048,lo,x+.048,hi,-.04,projection,CORNICE,'Paired stepped bracket',step)
    # Close the cut on its own shallow back. All external apertures retain real recesses.
    rectangle(b,-HALF,0,HALF,HEIGHT,-1.18,-1.12,REAR,'Plain back at cut',step)
    for x in (-HALF,HALF):
        rectangle(b,x-.032,0,x+.032,HEIGHT,-1.18,-.36,REAR,'Plain end at cut',step)
    rectangle(b,-HALF,HEIGHT-.09,HALF,HEIGHT,-1.18,0,REAR,'Roof return',step)
    for part in b.parts:
        if part['material']==STONE:
            part['texcoords']=[wall_uv(*v) for v in part['vertices']]
