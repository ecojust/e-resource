"""Recessed garden wings from two photographs; the right wing has only a single clear view."""
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from garden_plane import hit,straight_window
from garden_sashes import insert_sash
from garden_front import ANGLE,LEFT,LOW_WING_Z,ROOF_Z,STEP,curved_plan,slab
from materials import BASE,DARK,FRAME,GLASS,IRON,MID_GLASS,RENDER,ROOF,SILL,TRIM

CUT=3.15
RIGHT_FACE=1.45
RIGHT_EDGE=5.49
MAIN_END=curved_plan(0)[-1]

def short_volume(face,start,end,front_d,back_d,bottom,top,openings,label):
    f=face.face(0,front_d,1,0)
    f.solid(box(start,bottom,end,top).difference(unary_union(openings)),-.145,0,RENDER,label+' | front with deep openings')
    for u,d,ds in [(start,back_d,-1),(end,front_d,1)]:
        side=face.face(u,d,0,ds)
        side.rect(0,back_d-front_d,bottom,top,-.12,0,RENDER,label+' | return')
    face.face(end,back_d,-1,0).rect(0,end-start,bottom,top,-.10,0,BASE,label+' | recessed cut plane')
    slab(face,box(start,front_d,end,back_d),top-.055,top,ROOF,label+' | roof')
    return f

def main_shell(face,lod):
    arc=curved_plan(0,lod=lod);u_end,d_end=arc[-1]
    for left,right,z,outline in [(STEP,u_end,ROOF_Z,[(STEP,0),*arc,(u_end,CUT),(STEP,CUT)]),
                                   (LEFT,STEP,LOW_WING_Z,[(LEFT,0),(STEP,0),(STEP,CUT),(LEFT,CUT)])]:
        shape=Polygon(outline)
        slab(face,shape,z-.12,z-.044,ROOF,'streetward documented garden block | roof closure')
        slab(face,shape,.001,.03,BASE,'documented garden block | bottom closure')
        face.face(right,CUT,-1,0).rect(0,right-left,0,z,-.14,0,BASE,'visible garden section | rear cut')
    face.face(LEFT,CUT,0,-1).rect(0,CUT,0,LOW_WING_Z,-.16,0,RENDER,'left outer return')
    face.face(STEP,CUT,0,-1).rect(0,CUT,LOW_WING_Z,ROOF_Z,-.16,0,RENDER,'left stepped parapet return')
    face.face(u_end,d_end,0,1).rect(0,CUT-d_end,0,ROOF_Z,-.16,0,RENDER,'short return after the measured tangent')

def visible_right_wing(face,lod):
    f=face.face(0,RIGHT_FACE,1,0)
    x0=3.94;z_top=hit(509,114,RIGHT_FACE)[1]
    top=straight_window((491,145),(513,145),(519,178),(494,177),RIGHT_FACE)
    middle=straight_window((499,224),(523,224),(530,276),(504,275),RIGHT_FACE)
    # The left jamb disappears behind the circular end. The exposed upper profile and right jamb remain.
    a,b=4.00,5.31
    spring=hit(535,347,RIGHT_FACE)[1];crown=hit(514,318,RIGHT_FACE)[1]
    from math import pi,cos,sin
    n=12 if lod else 26
    crownline=[((a+b)/2+(b-a)*cos(i*pi/n)/2,spring+(crown-spring)*sin(i*pi/n)) for i in range(n+1)]
    portal=Polygon([(a,.01),(b,.01),*crownline])
    short_volume(face,x0,RIGHT_EDGE,RIGHT_FACE,CUT,0,z_top,[top,middle,portal],'right recessed wing')
    insert_sash(f,top,'right upper window',[.49],[.28],MID_GLASS)
    insert_sash(f,middle,'right middle window',[.48],[.35,.70],GLASS)
    f.solid(portal.buffer(.055,join_style=2).difference(portal),-.88,.03,TRIM,'right lower arch | rounded reveal')
    f.solid(portal,-.904,-.88,DARK,'right lower arch | shaded sectional closure')
    for v in [124,198,288]:
        z=hit(512,v,RIGHT_FACE)[1]
        f.rect(x0,RIGHT_EDGE,z-.017,z+.061,.002,.097,SILL,'right wing | projecting floor line')
    f.rect(x0,RIGHT_EDGE,z_top-.045,z_top+.03,.002,.095,TRIM,'right wing | roof rim')

def roof_steps(face,lod):
    # The broad steel window and top of the white roof canopy also appear in the 2017 background.
    d=2.53;upper=face.face(0,d,1,0)
    light=straight_window((231,55.5),(271.6,55.8),(271.2,92.2),(230.8,93.0),d)
    x_left=hit(213,80,d)[0]
    broad_head=11.98
    short_volume(face,x_left,-2.17,d,CUT,LOW_WING_Z,broad_head,[light],'rear high wing with broad garden window')
    insert_sash(upper,light,'broad steel roof casement',[.29,.56,.79],[.30,.76],MID_GLASS)
    edge_front=1.79
    edge_left=hit(205,32.8,edge_front)[0]
    slab(face,box(edge_left,edge_front,-2.05,CUT),broad_head-.19,broad_head,TRIM,'broad left wing | projecting horizontal roof')
    narrow_d=1.35
    small=straight_window((300,34.2),(326.5,35.3),(326.8,48.2),(300,47),narrow_d)
    f=short_volume(face,-2.42,.39,narrow_d,CUT,ROOF_Z,11.81,[small],'small upper room')
    insert_sash(f,small,'small upper window',[],[],GLASS)
    slab(face,box(-2.62,1.06,.52,CUT),11.81,12.035,TRIM,'top white canopy | fascia')
    slab(face,box(-2.66,1.01,.55,CUT),12.035,12.105,ROOF,'top white canopy | coping')
