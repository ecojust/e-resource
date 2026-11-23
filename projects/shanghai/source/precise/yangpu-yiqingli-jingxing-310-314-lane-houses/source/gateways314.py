"""Two differently treated side entrances in the frame of the 2015 photograph of lane 314."""
from math import cos, sin, pi
import numpy as np
from shapely.geometry import Polygon, LineString
from street314 import RED, GABLE, BASE, STONE, CAP, IRON, BROWN

def stepped_courses(w,left,right,top,bottom,count,label):
    # Each quoins block retains its own bevel and V joint on the exterior.
    pitch=(bottom-top)/count
    for i in range(count):
        a=top+i*pitch
        b=a+pitch
        w.block(left,a+.6,right,b-.6,-.42,.105,STONE,label+' quoin '+str(i+1))
        w.block(left+1.6,a+1.6,right-1.6,b-1.6,.103,.129,STONE,label+' dressed face '+str(i+1))
    w.block(left-2,bottom-11,right+2,bottom,-.43,.151,BASE,label+' plinth')

def scroll(w,x,y,size,mirror,label,lod):
    # A plastered scroll bears onto the plinth on the shoulder of each parapet.
    coords=[(0,0),(size*.15,-size*.11),(size*.41,-size*.05),
            (size*.66,size*.10),(size*.81,size*.43),(size,size*.60),(size,size*.90),(0,size*.90)]
    w.panel(w.poly([(x+mirror*a,y+b) for a,b in coords]),-.10,.071,STONE,label+' scroll body')
    ring=[]
    n=12 if lod else 24
    for i in range(n+1):
        theta=.25*pi+1.64*pi*i/n
        radius=size*(.235-.14*i/n)
        ring.append((x+mirror*size*.46+mirror*radius*cos(theta),y+size*.4+radius*sin(theta)))
    w.strip(ring,1.9,.070,.093,CAP,label+' scroll relief')

def right_portal(w,lod):
    tag='gateway on picture right'
    left,right=1049,1294
    stepped_courses(w,left,1097,467,696,9,tag+' left')
    stepped_courses(w,1246,right,467,696,9,tag+' right')
    w.block(left,448,right,468,-.42,.126,STONE,tag+' lintel')
    for x0,x1,y0,y1,d,m in [(1047,1297,435,448,.175,STONE),(1043,1300,428,437,.215,CAP),
                             (1040,1303,419,429,.254,STONE),(1036,1308,411,419,.282,CAP),
                             (1035,1307,405,412,.254,GABLE)]:
        w.block(x0,y0,x1,y1,-.40,d,m,tag+' crowning moulding')
    for i in range(18):
        x=1049+i*13.7
        w.block(x,433,x+6,440,.125,.216,STONE,tag+' dentils')
    # The pale central tablet carries no legible inscription in the original.
    w.block(1092,357,1250,405,-.26,.045,GABLE,tag+' parapet field')
    w.block(1112,363,1230,399,.039,.073,STONE,tag+' plain tablet')
    for x in [1092,1235]:
        w.block(x,358,x+8,403,.042,.089,STONE,tag+' tablet upright')
    for a,b in [(1049,1093),(1247,1294)]:
        w.block(a,373,b,404,-.28,.069,STONE,tag+' shoulder')
        w.block(a-4,370,b+3,375,-.29,.113,GABLE,tag+' shoulder cap')
    scroll(w,1090,359,24,-1,tag+' left',lod)
    scroll(w,1248,359,24,1,tag+' right',lod)
    w.block(1088,351,1254,357,-.26,.096,CAP,tag+' flat cap')
    # A shallow inner lining preserves the visible thickness of the open portal.
    w.block(1094,466,1098,695,-1.10,-.30,BROWN,tag+' left lining')
    w.block(1243,466,1247,695,-1.10,-.30,BROWN,tag+' right lining')
    w.block(1094,461,1247,467,-1.1,-.29,CAP,tag+' soffit')

def left_portal(w,lod):
    tag='gateway on picture left'
    for a,b in [(-41,-13),(51,72)]:
        w.block(a,466,b,697,-.44,.044,STONE,tag+' jamb')
        w.block(a+2,464,a+6,697,.043,.066,BASE,tag+' jamb edge')
    w.block(-41,439,72,467,-.41,.07,CAP,tag+' broad lintel')
    w.block(-43,431,73,439,-.43,.14,STONE,tag+' lower cornice')
    w.block(-18,386,72,431,-.26,.035,GABLE,tag+' red tablet surround')
    w.block(-4,399,46,430,.034,.062,STONE,tag+' lower blank tablet')
    w.block(-15,392,71,398,-.26,.130,CAP,tag+' tablet cap')
    w.block(-17,354,56,392,-.25,.055,RED,tag+' upper brick face')
    w.block(-18,351,57,356,-.27,.115,CAP,tag+' upper cornice')
    scroll(w,49,373,24,1,tag+' curved end',lod)
    w.block(-41,365,-19,433,-.35,.056,RED,tag+' projecting end pier')
    w.block(-43,361,-18,366,-.35,.108,CAP,tag+' pier cap')
    w.block(49,466,52,696,-.90,-.33,BROWN,tag+' passage lining')
    w.block(-41,463,72,467,-.9,-.34,CAP,tag+' soffit')

def add_gateways(w,lod):
    left_portal(w,lod)
    right_portal(w,lod)
