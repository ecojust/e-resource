"""Black cast-metal entrance recorded from Wuyuan Road in Antigng's 2017 photograph."""
from math import cos,sin,pi
import numpy as np
from shapely.geometry import box,LineString,Point
from shapely.ops import unary_union
from materials import rgb
FIELD='Maresca | blackened gate fields'
CAST='Maresca | black cast relief'
EDGE='Maresca | worn metal edges'
PALETTE={FIELD:rgb((45,47,44),.70),CAST:rgb((57,59,55),.52),EDGE:rgb((78,80,73),.48)}
WIDTH,HEIGHT=2.80,2.16
def frame(g,u0,z0,u1,z1,w,back,front,mat,tag):
    ring=box(u0,z0,u1,z1).difference(box(u0+w,z0+w,u1-w,z1-w))
    g.solid(ring,back,front,mat,tag)
def scroll_panel(g,x,z,width,height,lod):
    g.rect(x-width/2,x+width/2,z-height/2,z+height/2,-.018,-.010,FIELD,'inset of cast-gate panel')
    frame(g,x-width/2,z-height/2,x+width/2,z+height/2,.013,-.007,.003,CAST,'raised field edge')
    lines=[]
    for y in ((0.,) if lod else (-.28,.0,.28)):
        for sign in (-1,1):
            pts=[]
            for t in np.linspace(0,1,9 if lod else 17):
                angle=pi*(.25+1.60*t)
                r=(.37-.23*t)*width
                pts.append((x+sign*(.14*width+r*cos(angle)),z+y*height+.62*r*sin(angle)))
            lines.append(LineString(pts).buffer(.007 if lod else .006,cap_style=2,join_style=2))
    tracery=unary_union(lines).intersection(box(x-width*.45,z-height*.47,x+width*.45,z+height*.47))
    g.solid(tracery,.004,.014,CAST,'paired C-scrolls in the gate fields')
def key_course(g,a,b,z,lod):
    if lod:
        g.rect(a,b,z,z+.015,.014,.020,EDGE,'simplified raised horizontal border')
        return
    teeth=round((b-a)/.095)
    if teeth<1:return
    stride=(b-a)/teeth;line=[]
    for i in range(teeth):
        x=a+i*stride
        line.extend([(x,z),(x+.10*stride,z),(x+.10*stride,z+.029),(x+.70*stride,z+.029),
                      (x+.70*stride,z+.012),(x+.42*stride,z+.012),(x+.42*stride,z),(x+stride,z)])
    g.band(line,.006,.014,.020,EDGE,'meander border around iron leaf')
def add_gate(f,lod=False):
    # The dark 2017 street elevation is 1.30±0.04 times as wide as high.
    # The gate centre is the independent mapped north entry. Its metric
    # height is estimated. The leftmost lower corner is hidden by a tree.
    g=f.face(11.77,-3.19,0,1)
    halves=[(.0,1.371,[.20,.635,.97]),(1.392,WIDTH,[1.67,1.96,2.25,2.55])]
    for a,b,cols in halves:
        g.rect(a,b,.04,HEIGHT,-.066,-.020,FIELD,'street-facing iron leaf')
        frame(g,a,.045,b,HEIGHT,.066,-.018,.012,CAST,'outer gate-leaf frame')
        for z in (.075,1.035,2.064):key_course(g,a+.040,b-.040,z,lod)
        for z in (.548,1.57):
            for cx in cols:scroll_panel(g,cx,z,.181 if len(cols)==4 else .202,.61 if z<1 else .67,lod)
        for x in (a+.055,b-.055):
            g.rect(x-.009,x+.009,.12,2.055,.007,.017,EDGE,'vertical cast border')
    # The narrow inset pedestrian leaf starts inside the left leaf.
    frame(g,.421,.061,1.329,2.107,.017,.017,.029,EDGE,'pedestrian wicket within left leaf')
    for x in [1.283,1.480]:
        ros=Point(x,1.095).buffer(.055,quad_segs=10).difference(Point(x,1.095).buffer(.030,quad_segs=8))
        g.solid(ros,.031,.050,EDGE,'cast handle rose')
        g.rail([(x,-.055,1.062),(x,-.076,1.039),(x,-.080,1.013),(x,-.06,.995)],.009,EDGE,'door pull',8)
