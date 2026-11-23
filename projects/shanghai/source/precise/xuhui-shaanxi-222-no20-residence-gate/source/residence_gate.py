"""Reconstruct No. 20's portal, rectangular head panel and rounded double-door reveal."""
from math import cos, pi, sin
import numpy as np
from shapely.geometry import Polygon, box as rectangle
from gate_frieze import finish

WALL='Shaanxi 222-20 | pale enclosure render'
SHAFT='Shaanxi 222-20 | blue grey pier'
RETURN='Shaanxi 222-20 | rounded grey door reveal'
DARK='Shaanxi 222-20 | charcoal double door'
SEAM='Shaanxi 222-20 | door joint'
PANEL='Shaanxi 222-20 | dark rectangular head panel'
PANEL_EDGE='Shaanxi 222-20 | narrow head panel reveal'
COPING='Shaanxi 222-20 | pale upper coping'
PALETTE={WALL:finish((198,188,160),.94),SHAFT:finish((99,105,117),.91),
         RETURN:finish((138,134,121),.95),DARK:finish((37,34,34),.83),SEAM:finish((21,20,20),.95),
         PANEL:finish((65,64,61),.93),PANEL_EDGE:finish((107,102,86),.92),COPING:finish((172,168,154),.95)}
OUTER=(-.815,.859,2.300,.216)
INNER=(-.763,.817,2.245,.178)
DOOR_Y=.12
def path(profile,n):
    left,right,top,radius=profile
    pts=[(right,0.)]
    for cx,start in ((right-radius,0),(left+radius,pi/2)):
        for k in range(n+1):
            a=start+k*pi/(2*n)
            pts.append((cx+radius*cos(a),top-radius+radius*sin(a)))
    pts.append((left,0.))
    return pts

def prism(b,geom,y0,y1,mat,tag):
    b.prism(geom,-y1,-y0,lambda x,z,d:(x,-d,z),mat,'No. 20 | '+tag)
def block(b,x0,x1,y0,y1,z0,z1,mat,tag):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label='No. 20 | '+tag)
def band(b,rings,mat,tag,loop=False):
    count=len(rings[0]);verts=[p for ring in rings for p in ring];faces=[]
    for i in range(len(rings)):
        j=(i+1)%len(rings)
        for k in range(count if loop else count-1):
            l=(k+1)%count
            faces.append((i*count+k,i*count+l,j*count+l,j*count+k))
    if not loop:
        faces.extend([tuple(i*count for i in range(len(rings))),
                      tuple(reversed([i*count+count-1 for i in range(len(rings))]))])
    points=np.asarray(verts)-verts[0]
    vol=sum(points[f[0]]@np.cross(points[f[i]],points[f[i+1]]) for f in faces for i in range(1,len(f)-1))
    if vol<0:faces=[f[::-1] for f in faces]
    b.add(verts,faces,mat,'No. 20 | '+tag)
def at_y(row,y):
    return [(x,y,z) for x,z in row]
def shoulder(b,left,right,name):
    profile=[(2.678,.0,.073),(2.69,.008,.082),(2.724,.026,.113),
             (2.741,.046,.139),(2.777,.05,.142),(2.795,.04,.123),(2.804,.024,.106)]
    rings=[]
    for z,offset,depth in profile:
        rings.append([(left-offset,.012,z),(left-offset,-depth,z),(right+offset,-depth,z),(right+offset,.012,z)])
    faces=[(3,2,1,0)]
    for i in range(len(rings)-1):
        for k in range(4):faces.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
    faces.append(tuple(range(4*(len(rings)-1),4*len(rings))))
    b.add([v for r in rings for v in r],faces,SHAFT,'No. 20 | '+name+' shouldered capital')
def add_entry(b,lod=False):
    n=10 if lod else 22
    outer=path(OUTER,n);inner=path(INNER,n)
    panel=rectangle(-.802,2.806,.870,3.267)
    wall=rectangle(-1.97,0,2.08,4.645).difference(Polygon(outer)).difference(panel)
    prism(b,wall,0,.235,WALL,'enclosure with cut openings')
    # A closed splayed surround has independently measured front and rear arrises.
    band(b,[at_y(outer,-.001),at_y(inner,DOOR_Y-.006),at_y(inner,DOOR_Y+.012),
            at_y(outer,DOOR_Y+.012)],RETURN,'rounded door reveal')
    leaf=Polygon(inner); join=.025
    for side,span in [('left',(-1.2,join-.003)),('right',(join+.003,1.2))]:
        prism(b,leaf.intersection(rectangle(span[0],-.10,span[1],2.5)),DOOR_Y,DOOR_Y+.055,DARK,side+' dark door leaf')
    block(b,join-.005,join+.005,DOOR_Y+.006,DOOR_Y+.056,.004,2.242,SEAM,'double leaf meeting stile')
    # Two source photographs show a dark field with a narrow setback and crossing utility wires.
    # Its face carries no legible word or verified permanent grille.
    inner_panel=rectangle(-.782,2.826,.850,3.246)
    prism(b,panel.difference(inner_panel),.002,.062,PANEL_EDGE,'narrow panel rebate')
    prism(b,inner_panel,.043,.085,PANEL,'recessed rectangular head panel')
    for name,left,right in [('left',-1.520,-.970),('right',1.044,1.618)]:
        block(b,left,right,-.077,.011,0,2.688,SHAFT,name+' tall pier')
        shoulder(b,left,right,name)
        block(b,left+.013,right-.012,-.090,.012,2.795,3.330,SHAFT,name+' short upper pier')
    block(b,-1.97,2.08,-.009,.244,4.47,4.497,COPING,'lower coping fillet behind cornice')
    block(b,-1.97,2.08,-.019,.251,4.584,4.67,COPING,'weathered upper cap behind cornice')
