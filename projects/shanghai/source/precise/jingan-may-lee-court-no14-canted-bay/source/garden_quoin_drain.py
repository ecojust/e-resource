"""Alternating dressed corner courses and the photographed offset rainwater pipe."""
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
HIGHLIGHT = "Garden corner | warm dressed stone"
PALE = "Garden corner | pale buff dressed stone"
GREY = "Garden corner | cool grey dressed stone"
PIPE = "Garden corner | brown-black downpipe"
HOPPER = "Garden corner | weathered square rainwater head"
RIM = "Garden corner | iron rim and pipe joints"
NECK = "Garden corner | folded outlet neck"
CODE = HERE.parent / "measurements/garden-quoin-drain.json"


def surface(rgb, roughness, metallic=0):
    srgb = [v/255 for v in rgb]
    linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in srgb]
    return {"color":linear, "roughness":roughness, "metallic":metallic}


PALETTE = {HIGHLIGHT:surface((204,196,174),.92), PALE:surface((197,189,171),.90),
           GREY:surface((190,184,170),.93), PIPE:surface((67,59,49),.77,.23),
           HOPPER:surface((62,51,41),.74,.22), RIM:surface((90,77,61),.71,.28),
           NECK:surface((79,70,59),.72,.30)}


def horizontal_course(builder, corner, front, side, relief, bottom, top, mat, name):
    """Make one bonded L-shaped block or its visible front leg behind foliage."""
    x,y = corner
    inside = .008
    def outline(bevel,z):
        west = -relief + bevel
        south = -relief + bevel
        end = front - bevel
        inset = inside - bevel
        if side is None:
            xy = [(west,south),(end,south),(end,inset),(west,inset)]
        else:
            far = side - bevel
            xy = [(west,south),(end,south),(end,inset),(inset,inset),(inset,far),(west,far)]
        return [(x+u,y+v,z) for u,v in xy]
    # The narrow bevel catches the light on each facing and leaves a real shadow joint.
    bevel = .006
    rings = [outline(bevel,bottom), outline(0.,bottom+.008),
             outline(0.,top-.008), outline(bevel,top)]
    n = len(rings[0])
    cap = [(0,1,3),(1,2,3),(0,3,5),(3,4,5)] if n == 6 else [(0,1,2),(0,2,3)]
    faces = [tuple(reversed(f)) for f in cap] + [tuple(3*n+i for i in f) for f in cap]
    for i in range(3):
        for j in range(n):
            k=(j+1)%n
            faces.append((i*n+j,i*n+k,(i+1)*n+k,(i+1)*n+j))
    builder.add([v for ring in rings for v in ring],faces,mat,name)


def rectangular_ring(cx,cy,z,width,depth):
    return [(cx+sx*width/2,cy+sy*depth/2,z) for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1))]


def hopper_shell(builder, sections, metal_thickness, mat, name):
    """Folded open-topped quadrilateral head, keeping the throat open at the pipe."""
    ex=[rectangular_ring(*section) for section in sections]
    inside=[rectangular_ring(cx,cy,z,w-2*metal_thickness,d-2*metal_thickness)
            for cx,cy,z,w,d in sections]
    rings = ex + list(reversed(inside))
    faces=[]
    for i in range(len(rings)):
        k=(i+1)%len(rings)
        for j in range(4):
            nxt=(j+1)%4
            faces.append((4*i+j,4*i+nxt,4*k+nxt,4*k+j))
    builder.add([p for ring in rings for p in ring],faces,mat,name)


def add_quoin_drain(builder,lod=False):
    data=json.loads(CODE.read_text())
    far=lod is True or lod in ("lod","low","far","distant")
    base=data["corner_xy_m"]
    relief=data["stone_relief_m"]
    for row in data["courses"]:
        top,bottom = row["top_bottom_z_m"]
        i = row["course_from_top"]
        stone = [PALE,HIGHLIGHT,PALE,GREY,HIGHLIGHT,PALE][(i-1)%6]
        horizontal_course(builder, base, row["front_length_m"],row["return_length_m"],
                          relief,bottom+.0045,top-.0045,stone,f"Garden corner | bonded quoin course {i:02}")
    low,high=data["shaded_unjointed_head_z_m"]
    horizontal_course(builder,base,.306,.281,relief,low+.0045,high,GREY,
                      "Garden corner | shaded upper stone surface below the soffit")
    pipe=data["pipe"]
    radius=pipe["shaft_radius_m"]
    shaft=np.asarray(pipe["shaft_xyz_m"])
    sections=10 if far else 20
    builder.tube(shaft[::-1],radius,PIPE,sections,"Garden corner | vertical iron pipe ending at foliage")
    rims=np.asarray(pipe["hopper_upper_ring_xyz_m"])
    cx,cy,z=rims.mean(axis=0)
    span=np.ptp(rims,axis=0)
    x0,y0,z0=shaft[0]
    throat=(x0,y0,z0-.018,2*radius+.008,2*radius+.010)
    shoulder=(cx-.015,cy,z-.073,span[0]-.036,span[1]-.019)
    rim=(cx,cy,z,span[0],span[1])
    hopper_shell(builder,[throat,shoulder,rim],.010,HOPPER,"Garden corner | tapered hopper with square rim")
    hopper_shell(builder,[(cx,cy,z-.020,span[0]+.012,span[1]+.012),
                          (cx,cy,z+.006,span[0]+.012,span[1]+.012)],
                 .008,RIM,"Garden corner | folded lip on hopper")
    neck=np.asarray(pipe["bent_neck_xyz_m"])
    builder.tube(neck[::-1],radius*.79,NECK,sections,"Garden corner | offset neck from eaves into rainwater head")
    for name,upper,lower in [("eaves collar",neck[0],neck[1]),("pipe collar below head",shaft[0],shaft[1])]:
        direction=lower-upper
        length=np.linalg.norm(direction)
        a=upper+direction/length*.022
        b=upper+direction/length*(.102 if name=="eaves collar" else .065)
        rad=radius*(.94 if name=="eaves collar" else 1.09)
        builder.tube([a,b],rad,RIM,sections,"Garden corner | "+name)
    height=pipe["visible_joint_z_m"]
    lo=shaft[-1];hi=shaft[-2]
    center=lo+(hi-lo)*(height-lo[2])/(hi[2]-lo[2])
    builder.tube([center-[0,0,.019],center+[0,0,.019]],radius*1.07,RIM,sections,
                 "Garden corner | observed lower shaft joint")
