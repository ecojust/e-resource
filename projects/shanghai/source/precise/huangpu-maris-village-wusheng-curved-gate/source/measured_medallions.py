"""Make the four black disks and the separately editable gilt characters of the north gate."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Point,Polygon
from photo_architecture import Facade

MEASUREMENTS=Path(__file__).resolve().parents[1]/'measurements/gate-medallions.json'
BACK='Wrought sign edge'
DISK='Black painted sign disks'
GILT_SIDE='Shadowed gilt edges'
GILT='Raised gilt letters'
def color(rgb,roughness,metallic):
    s=np.array(rgb)/255.
    return dict(color=np.where(s<.04045,s/12.92,((s+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)
PALETTE={BACK:color([38,39,39],.72,.25),DISK:color([30,33,35],.68,.22),
         GILT_SIDE:color([151,116,67],.58,.40),GILT:color([199,167,105],.47,.48)}
def shape_outline(group,position,radius):
    def scale(ring):
        return [(position[0]+x*radius,position[1]+z*radius)for x,z in ring]
    return Polygon(scale(group['shell']),[scale(h)for h in group['holes']]).buffer(0)
def add_medallions(builder,lod):
    f=Facade(builder,(-4,0),(4,0),'Wusheng gate medallions')
    report=json.loads(MEASUREMENTS.read_bytes())
    for k,rec in enumerate(report['letters'],1):
        centre=rec['centre_xz_m'];radius=rec['radius_m'];label='disc '+str(k)
        disk=Point(*centre).buffer(radius,quad_segs=12 if lod else 28)
        f.prism(disk,-.006,.025,BACK,label+' edge')
        f.prism(disk.buffer(-.003),.025,.026,DISK,label+' black face')
        for j,g in enumerate(rec['outline'],1):
            outline=shape_outline(g,centre,radius)
            if lod:outline=outline.simplify(.0012,preserve_topology=True)
            mark='letter '+str(k)+' stroke '+str(j)
            f.prism(outline,.026,.037,GILT_SIDE,mark+' edge')
            top=outline.buffer(-.0008,join_style='round',quad_segs=2)
            if not top.is_empty:f.prism(top,.037,.0385,GILT,mark+' face')
