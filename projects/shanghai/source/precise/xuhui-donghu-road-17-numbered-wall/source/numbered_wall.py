"""Photo-informed exhibit of the public street wall carrying the Donghu Road 17 plate."""
from math import hypot
from pathlib import Path
from random import Random

from shapely import affinity
from shapely.geometry import Polygon, box
from photo_architecture import Facade
from sign_lettering import lettering_shapes

HERE = Path(__file__).resolve().parent
RED = 'Burnt red horizontal facing'
RECESS = 'Shadow in the facing courses'
STONE = 'Warm grey stone aggregate'
DARK_GRAIN = 'Dark mineral flecks'
LIGHT_GRAIN = 'Pale mineral flecks'
SOFFIT = 'Underside of stone course'
PLATE = 'Weathered green number plate'
EDGE = 'Dark enamel edge'
LETTER = 'Cream address characters'
PALETTE = {
    name: {'color': color, 'roughness': roughness}
    for name,color,roughness in [
        (RED,[.48,.205,.145],.86),(RECESS,[.19,.107,.086],.94),
        (STONE,[.60,.59,.55],.94),(DARK_GRAIN,[.385,.384,.362],.95),
        (LIGHT_GRAIN,[.72,.706,.655],.94),(SOFFIT,[.41,.40,.372],.94),
        (PLATE,[.064,.246,.185],.48),(EDGE,[.049,.129,.106],.62),
        (LETTER,[.89,.846,.645],.60),
    ]
}

# The plate is a scale assumption. The photographed wall base lies below the crop.
PLATE_WIDTH = .32
PLATE_HEIGHT = .22
PLATE_Z = .78
BOTTOM = 0.
BRICK_TOP = PLATE_Z+.232
STONE_BREAK = PLATE_Z+.316
UPPER_BEAD = PLATE_Z+.652
CAP_BOTTOM = PLATE_Z+.771
TOP = PLATE_Z+.851
START = (-1.015,0.)
BEND = (.275,0.)
END = (.575,.420)
ANCHORS = (START,BEND,END)

def unit_tangent(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    norm=hypot(dx,dy)
    return dx/norm,dy/norm

def offset(distance):
    first=unit_tangent(START,BEND)
    last=unit_tangent(BEND,END)
    nx,ny=first[1],-first[0]
    mx,my=last[1],-last[0]
    denom=1+nx*mx+ny*my
    return [(START[0]+nx*distance,START[1]+ny*distance),
            (BEND[0]+(nx+mx)*distance/denom,BEND[1]+(ny+my)*distance/denom),
            (END[0]+mx*distance,END[1]+my*distance)]

def band(builder,label,material,z0,z1,outer,inner=-.16):
    polygon=Polygon(offset(outer)+list(reversed(offset(inner))))
    builder.prism(polygon,z0,z1,lambda x,y,z:(x,y,z),material,label)

def front_shapes():
    # Two independent outlines reflect the forms visible on the plate in figure 37.
    one=Polygon([(0,.105),(.020,.118),(.035,.120),(.046,.023),(.063,.022),(.063,.005),(.005,.005),(.005,.022),(.020,.023),(.012,.090),(.002,.083)])
    seven=Polygon([(.074,.118),(.145,.118),(.145,.102),(.115,.004),(.091,.004),(.120,.096),(.074,.096)])
    return [affinity.translate(p,xoff=-.074,yoff=-.018)for p in (one,seven)]

def plate(face):
    centre=-(START[0]+BEND[0])/2
    face.prism(box(centre-.162,PLATE_Z-.112,centre+.162,PLATE_Z+.112),.005,.013,EDGE,'Number plate folded edge')
    face.prism(box(centre-.16,PLATE_Z-.11,centre+.16,PLATE_Z+.11),.013,.016,PLATE,'Green face')
    for idx,outline in enumerate(front_shapes()):
        shifted=affinity.translate(outline,xoff=centre,yoff=PLATE_Z)
        face.prism(shifted,.016,.0168,LETTER,'Address numeral '+str(idx+1))
    for index,(_,glyph) in enumerate(lettering_shapes('东湖路',.205,.050,font=HERE/'fonts/DonghuAddress.otf')):
        face.prism(affinity.translate(glyph,xoff=centre,yoff=PLATE_Z-.077),.016,.0168,LETTER,'Street name '+str(index+1))

def make_aggregate(builder,lod):
    random=Random(351)
    for face_no,(start,end) in enumerate(zip(ANCHORS,ANCHORS[1:])):
        face=Facade(builder,start,end,'Wall '+str(face_no+1))
        triangles={DARK_GRAIN:([],[]),LIGHT_GRAIN:([],[])}
        # Individual aggregate grains stay out of the projecting joints and shadow bands.
        n=int(face.length*(195 if lod else 1900))
        for _ in range(n):
            z=random.uniform(BRICK_TOP+.012,TOP-.004)
            if STONE_BREAK-.006<z<STONE_BREAK+.009 or UPPER_BEAD-.011<z<UPPER_BEAD+.011 or CAP_BOTTOM-.010<z<CAP_BOTTOM+.012:continue
            surface=.017 if z<STONE_BREAK else (.031 if z<UPPER_BEAD else (.049 if z<CAP_BOTTOM else .070))
            u=random.uniform(-face.length*.492,face.length*.492)
            r=random.uniform(.0009,.0027)*(1.7 if lod else 1)
            color=DARK_GRAIN if random.random()<.67 else LIGHT_GRAIN
            verts,faces=triangles[color]
            i=len(verts)
            for du,dz in ((-.80*r,-.56*r),(.86*r,-.34*r),(.12*r,r)):
                verts.append(tuple(face.point(u+du,z+dz,surface+.00022)))
            faces.append((i,i+1,i+2))
        for color,(verts,faces) in triangles.items():
            builder.add(verts,faces,color,f'Stone {face_no+1}/{color}')

def add_building(builder,lod):
    pitch=.0743
    # Outward faces of the horizontal facing strips project slightly beyond the open raked joints.
    band(builder,'Continuous backing of scribed red wall',RECESS,BOTTOM,BRICK_TOP,-.007)
    top=BRICK_TOP
    row=0
    while top>BOTTOM:
        low=max(BOTTOM,top-pitch)
        face_low=low if low==BOTTOM else low+.0024
        band(builder,f'Horizontal facing course {row+1:02d}',RED,face_low,top-.0012,0.,-.007)
        top=low
        row+=1
    band(builder,'Lower shoulder of stone band',STONE,BRICK_TOP,STONE_BREAK-.004,.017)
    band(builder,'Recess below main stone band',SOFFIT,STONE_BREAK-.004,STONE_BREAK+.005,.022)
    band(builder,'Main dressed stone belt',STONE,STONE_BREAK+.005,UPPER_BEAD-.006,.031)
    band(builder,'Recess beneath upper roll',SOFFIT,UPPER_BEAD-.006,UPPER_BEAD+.006,.038)
    band(builder,'Upper square-faced stone bead',STONE,UPPER_BEAD+.006,CAP_BOTTOM-.006,.049)
    band(builder,'Coping soffit',SOFFIT,CAP_BOTTOM-.006,CAP_BOTTOM+.009,.059)
    band(builder,'Upper stone coping slab',STONE,CAP_BOTTOM+.009,TOP,.070,-.177)
    for face_no,(a,b) in enumerate(zip(ANCHORS,ANCHORS[1:])):
        face=Facade(builder,a,b,'Wall '+str(face_no+1))
        # Stone bedding joints can be read across the belt at the face change.
        lengths=(-face.length/2+.024,face.length/2-.026) if face_no==0 else (-face.length/2+.235,)
        for number,u in enumerate(lengths):
            for n,(z0,z1,d) in enumerate(((BRICK_TOP,STONE_BREAK-.004,.017),(STONE_BREAK+.005,UPPER_BEAD-.006,.031),(UPPER_BEAD+.006,CAP_BOTTOM-.006,.049),(CAP_BOTTOM+.009,TOP,.070))):
                face.prism(box(u-.0018,z0,u+.0018,z1),d,d+.00025,SOFFIT,f'Stone seam {number+1}-{n+1}')
        if face_no==0:
            plate(face)
    make_aggregate(builder,lod)
