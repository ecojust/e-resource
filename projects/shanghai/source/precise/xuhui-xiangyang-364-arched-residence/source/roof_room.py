"""Photographed roof room, including the south return to its last unobscured coping point."""
import json
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
from materials import PLASTER,CEMENT,DARK,GLASS,FRAME,ROOF,SHADOW

SURVEY=json.loads((Path(__file__).resolve().parents[1]/'measurements/roof-room-two-stations.json').read_text())

def add_roof_room(front,lod=False):
    q=SURVEY['parameters'];south,north=q['south'],q['north'];depth=q['front_d']
    z=q['coping_z'];base=10.22;back=SURVEY['south_side_visible']['depth_cut_m'];thick=.17
    f=front.face(0,depth,1,0)
    openings=[box(q[part+'_x'],q['window_sill'],q[part+'_x']+q[part+'_width'],q['window_head'])for part in ['left','right']]
    wall=box(south+.06,base,north-.06,z-.16)
    f.solid(wall.difference(unary_union(openings)),-thick,0,PLASTER,'raised roof room | front')
    for part,rect in zip(['south','north'],openings):
        x0,z0,x1,z1=rect.bounds;h=z1-z0;cx=(x0+x1)*.5
        f.solid(rect,-.143,-.121,GLASS,part+' roof-room light | blue grey glass')
        f.solid(rect.difference(rect.buffer(-.034,join_style=2)),-.119,-.080,FRAME,part+' roof-room light | steel sash')
        f.rect(cx-.011,cx+.011,z0+.025,z1-.025,-.119,-.091,FRAME,part+' roof-room light | upright')
        for i,v in enumerate((.37,.74)):
            f.rect(x0+.024,x1-.024,z0+h*v-.013,z0+h*v+.013,-.117,-.085,FRAME,part+f' roof-room light | rail {i+1}')
        f.rect(x0-.05,x1+.05,z0-.055,z0,-.085,.033,CEMENT,part+' roof-room light | sill')
    # Walls annotated on the south/front photographs. The back is a recessed sectional closure.
    southwall=front.face(south+.06,back,0,-1)
    northwall=front.face(north-.06,depth+thick,0,1)
    length=back-depth-thick
    southwall.rect(0,length,base,z-.16,-thick,0,PLASTER,'raised roof room | photographed south wall')
    northwall.rect(0,length,base,z-.16,-thick,0,PLASTER,'raised roof room | short return')
    rear=front.face(north-.06-thick,back,-1,0)
    rear.rect(0,north-south-.12-2*thick,base,z-.16,-.075,0,SHADOW,'raised roof room | cut at last visible depth')
    for lo,hi,extend,mat,name in [(z-.16,z-.115,.012,CEMENT,'neck'),(z-.115,z-.045,.035,DARK,'dark cornice'),(z-.045,z,.060,ROOF,'coping')]:
        front.rect(south+.06-extend,north-.06+extend,lo,hi,-back,-depth+extend,mat,'raised roof room | '+name)
