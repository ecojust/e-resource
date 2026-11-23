"""Visible plaster, steel casements, projecting hoods and courtyard boundary of Qixia Village."""
import json
from pathlib import Path
import sys
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent;MEASURE=HERE.parent/'measurements'
sys.path.insert(0,str(MEASURE))
from register_court import Camera
from no7_enclosure import finish
WALL='Qixia | buff roughcast';TRIM='Qixia | blue-grey sill and eave'
STEEL='Qixia | dark wine-painted casements';GLASS='Qixia | muted steel-blue glazing'
REVEAL='Qixia | shaded reveal';HOOD='Qixia | weathered grey hood';PIPE='Qixia | pale rain leader'
FENCE='Qixia | yellow courtyard enclosure';PIER='Qixia | slate grey gate posts'
DOOR='Qixia | dark courtyard gate';SIGN='Qixia | green enamel plate';INK='Qixia | cream enamel lettering'
PALETTE={WALL:finish((201,192,156),.94),TRIM:finish((148,155,159),.93),STEEL:finish((82,66,62),.65,.12),
         GLASS:finish((107,121,123),.35,.1),REVEAL:finish((66,66,58),.96),HOOD:finish((109,121,112),.80),
         PIPE:finish((200,200,184),.81),FENCE:finish((196,184,141),.94),PIER:finish((149,151,147),.90),
         DOOR:finish((56,56,51),.82),SIGN:finish((42,108,83),.50,.14),INK:finish((210,222,182),.70)}
SURVEY=json.loads((MEASURE/'front-window-pixels.json').read_text())
FIT=json.loads((MEASURE/'court-cameras.json').read_text())
F67=-FIT['balcony_projection_m'];F9=-FIT['no9_balcony_projection_m'];BACK=.69

def slab(b,l,r,f,t,low,high,mat,name):
    if l>=r or f>=t or low>=high:return
    b.box(((l+r)/2,(f+t)/2,(low+high)/2),(r-l,t-f,high-low),mat,label=name)

def layer(b,shape,y,thick,mat,name):
    if not shape.is_empty:
        b.prism(shape,-y-thick,-y,lambda x,z,d:(x,-d,z),mat,name)

def limits(photo,quad,y):
    c=Camera(photo);q=np.array([c.wall(v,y)for v in quad])
    return [float(np.mean(q[[0,3],0])),float(np.mean(q[[2,3],2])),
            float(np.mean(q[[1,2],0])),float(np.mean(q[[0,1],2]))]

def window(b,obs,y,lod):
    photo,name,*data=obs; l,z,r,h=limits(photo,data[:4],y);cols,rows=data[4:]
    if h-z<.2 or r-l<.15:return
    opening=box(l,z,r,h);inner=box(l+.035,z+.035,r-.035,h-.035)
    layer(b,opening.difference(inner),y+.035,.077,STEEL,name+' | rolled perimeter')
    slab(b,l+.025,r-.025,y+.125,y+.140,z+.03,h-.03,GLASS,name+' | reflected daylight')
    for i in range(1,cols):
        x=l+(r-l)*i/cols;slab(b,x-.012,x+.012,y+.069,y+.095,z+.025,h-.025,STEEL,name+' | mullion')
    for i in range(1,rows):
        zz=z+(h-z)*i/rows;slab(b,l+.025,r-.025,y+.042,y+.070,zz-.012,zz+.012,STEEL,name+' | transom')
    slab(b,l-.045,r+.052,y-.085,y+.02,z-.062,z+.008,TRIM,name+' | sill')
    slab(b,l-.027,r+.031,y-.025,y+.011,h-.006,h+.04,WALL,name+' | shallow head')

def observed_x(photo,uv,y=0.):return float(Camera(photo).wall(uv,y)[0])

def height(x):
    # The eastern crest in frame 17 and the raised central parapet in 19 are distinct.
    ref=[(-29,9.04),(-16.7,9.04),(-12,8.94),(-10.6,9.14),(-6.9,9.31),(-4.8,8.43),
         (-2.55,7.96),(2.9,7.80),(7.1,7.8),(12.45,8.06)]
    return float(np.interp(x,*np.array(ref).T))

def architecture(b,lod):
    xcut=observed_x(20,(56,131));end=observed_x(17,(593,107))
    westmid=observed_x(20,(594,223),F9)
    green=observed_x(18,(333,312),F67)
    divide=observed_x(18,(552,35),F67)
    from no6_loggia import layout as six_layout, no6_rear_opening
    six=six_layout(Camera(17),F67,BACK);divide=six['left'];six_end=six['right']
    sections=[(xcut,westmid,BACK,'southwestern open terraces'),(westmid,green,0.,'paired steel-window range'),
              (green,divide,BACK,'No 7 terrace wall'),(divide,six_end,BACK,'No 6 recessed terrace wall'),
              (six_end,end,0.,'No 6 outer window range')]
    for l,r,y,name in sections:
        windows=[]
        for obs in SURVEY['field']+SURVEY['behind_open_balconies']:
            if obs[1] in ('9 right upper doorway partly visible','6 upper shaded terrace door'):continue
            if y==0 and obs in SURVEY['behind_open_balconies']:continue
            if y!=0 and obs in SURVEY['field']:continue
            p=limits(obs[0],obs[2:6],y)
            if l-.035<.5*(p[0]+p[2])<r+.035:windows.append((obs,p))
        breaks=[l]+[x for x in (-16.7,-12.,-10.6,-6.9,-4.8,-2.55,2.9,7.1) if l+.03<x<r-.03]+[r]
        outer=Polygon([(l,0),(r,0),*[(x,height(x))for x in breaks[::-1]]])
        holes=[box(*p) for _,p in windows]
        if name=='No 6 recessed terrace wall':
            door=no6_rear_opening(Camera(17),F67,BACK)
            holes.append(door)
            layer(b,door,BACK+.145,.025,REVEAL,'No 6 | dark glazed upper recess')
        holes=unary_union(holes)
        layer(b,outer.difference(holes),y,.215,WALL,'Courtyard front | '+name)
        for obs,_ in windows:window(b,obs,y,lod)
        for a,c in zip(breaks,breaks[1:]):
            q=Polygon([(a,height(a)-.070),(c,height(c)-.070),(c,height(c)+.035),(a,height(a)+.035)])
            layer(b,q,y-.11,.43,TRIM,name+' | parapet edge')
        # At a setback the flank is visible through the railings of the contiguous open decks.
    for x,y0,y1,label in [(westmid,0,BACK,'right end of open terraces'),(green,0,BACK,'green terrace return'),
                            (divide,F67,BACK,'divider between Nos 6 and 7'),(six_end,0,BACK,'No 6 return')]:
        slab(b,x-.08,x+.08,y0,y1,0,height(x),WALL,label)
    # Thin metal window hoods with projecting end brackets in the two photographs.
    for photo,points in [(19,[(170,180),(349,148)]),(19,[(174,57),(337,10)]),
                          (18,[(55,66),(203,50)]),(18,[(247,68),(313,62)]),(18,[(218,325),(339,315)])]:
        c=Camera(photo);v=[c.wall(uv,-.45)for uv in points]
        a,z=min(p[0] for p in v),np.mean([p[2]for p in v]);last=max(p[0]for p in v)
        slab(b,a,last,-.48,.025,z-.055,z,HOOD,'Court | flat projecting window hood')
        for x in [a+.075,last-.075]:
            b.tube([(x,-.02,z-.35),(x,-.44,z-.027)],.013,STEEL,sides=6,label='Court | sloping hood bracket')
    return dict(left=xcut,right=end,six_start=divide,six_end=six_end,no7_start=green,no9_end=westmid)
