"""The brick, lime panels, framing and recessed entrance on the documented courtyard elevation."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from service_materials import BRICK,PLASTER,FRAME,GLASS,DOOR,STONE,IRON

MEASUREMENTS=Path(__file__).resolve().parent.parent/'measurements'
def panel(b,geometry,y0,y1,material,label):
    b.prism(geometry,-y1,-y0,lambda x,z,d:(x,-d,z),material,'Eves courtyard / '+label)

def board(b,a,c,width,y0,y1,mat,label):
    a,c=np.asarray(a),np.asarray(c)
    tangent=c-a;normal=np.array([-tangent[1],tangent[0]])/np.linalg.norm(tangent)*width/2
    panel(b,Polygon([a+normal,a-normal,c-normal,c+normal]),y0,y1,mat,label)

def add_courtyard(b,frame,lod=False):
    obs=json.loads((MEASUREMENTS/'front-timber-controls.json').read_bytes())
    w,h=frame.width,frame.eave-.144
    a,c,height=frame.portal_left,frame.portal_right,frame.portal_top
    def elevation(uv):
        p=frame.design.wall(uv)
        return p[[0,2]]
    opening=box(a,0,c,height)
    # Brickwork and pale upper infill meet around one genuine open portal.
    front=box(0,0,w,h)
    ground=box(0,0,w,frame.rail).difference(opening)
    upper=front.difference(unary_union([ground,opening]))
    panel(b,ground,0,.24,BRICK,'ground-floor brick panels')
    panel(b,upper,.012,.24,PLASTER,'lime panels between oak members')
    for i,uv in enumerate(obs['full_posts']):
        x=elevation(uv)[0]
        if i==0:x=.09
        elif i==len(obs['full_posts'])-1:x=w-.09
        elif i==2:x=a-.075
        elif i==3:x=c+.075
        panel(b,box(x-.07,0,x+.07,h),-.052,.033,FRAME,'full-height courtyard post')
    for i,uv in enumerate(obs['belt_posts']):
        x=elevation(uv)[0]
        if x<=.06 or x>=w-.06:continue
        z0=height if a<x<c else frame.rail
        panel(b,box(x-.043,z0,x+.043,h),-.058,.020,FRAME,'upper vertical stud')
    for n,(uv1,uv2) in enumerate(obs['braces']):
        start,end=elevation(uv1),elevation(uv2)
        direction=end-start
        norm=np.array([-direction[1],direction[0]])/np.linalg.norm(direction)*.056
        outline=Polygon([start+norm,start-norm,end-norm,end+norm]).intersection(upper)
        if not outline.is_empty:panel(b,outline,-.065,.020,FRAME,'diagonal oak brace')
    panel(b,box(0,h-.119,w,h+.035),-.089,.048,FRAME,'eaves plate')
    for l,r in [(0,a),(c,w)]:
        panel(b,box(l,frame.rail-.067,r,frame.rail+.066),-.079,.041,FRAME,'rail between the brick and infill')
    panel(b,box(a-.12,height-.075,c+.12,height+.072),-.086,.12,FRAME,'higher lintel of central doorway')
    recess=.415
    for x in [a,c]:
        b.box([x,recess/2,height/2],[.15,recess+.025,height],FRAME,label='Eves central portal / boarded reveal')
    b.box([(a+c)/2,recess/2,height-.065],[c-a,recess+.025,.13],FRAME,label='Eves central portal / ceiling of entry')
    b.box([(a+c)/2,-.10,.044],[c-a+.30,.94,.088],STONE,label='Eves central portal / threshold')
    # The left leaf has a row of rectangular lights above solid lower panels.
    # Its counterpart falls in deep shade behind the figures in the proposal.
    mid=a+(c-a)*.49
    window=box(a+.09,height*.48,mid-.07,height-.16)
    left_leaf=box(a+.033,.09,mid,height-.11)
    panel(b,left_leaf.difference(window),recess,recess+.085,DOOR,'left door leaf with a glazed top')
    panel(b,window.buffer(.009,join_style=2),recess+.050,recess+.065,GLASS,'glass behind upper lights')
    for x in np.linspace(window.bounds[0],window.bounds[2],5):
        panel(b,box(x-.018,window.bounds[1],x+.018,window.bounds[3]),recess-.024,recess+.05,FRAME,'vertical glazing bar')
    panel(b,box(mid+.038,.08,c-.05,height-.105),recess+.07,recess+.153,DOOR,'recessed door in shade')
    for x in np.linspace(a+.14,mid-.15,5):
        panel(b,box(x-.021,.21,x+.021,height*.455),recess-.022,recess+.02,FRAME,'lower door panel joint')
    for l,r in [(a+.08,mid-.04),(mid+.075,c-.095)]:
        panel(b,box(l,.13,r,.205),recess-.024,recess+.018,FRAME,'lower door rail')
