"""Roof planes, weathered tile courses and three original brick stacks."""
import math
import numpy as np
from shapely.geometry import box

TILES=('old russet clay tile','warm brown plain tile','muted red roof tile')
UNDER='dark roof underlay'; EDGE='dark bargeboard'; BRICK='garden red face brick'; CAP='dark chimney cap'

def plane(b,quad,lod,label):
    """A plane from eave (first two vertices) to ridge, with staggered tile laps."""
    p,q,r,s=map(lambda v:np.array(v,float),quad)
    normal=np.cross(q-p,s-p);normal/=np.linalg.norm(normal)
    if normal[2]<0:normal*=-1
    bottom=[a-[0,0,.115]for a in (p,q,r,s)]
    b.add(list((p,q,r,s))+bottom,[(0,1,2,3),(7,6,5,4),(4,5,1,0),(5,6,2,1),(6,7,3,2),(7,4,0,3)],UNDER,label+'/overhanging soffit')
    bands=max(2,round(np.linalg.norm(s-p)/(.44 if lod else .235)))
    width=np.linalg.norm(q-p);pitch=.54 if lod else .28
    verts=[[]for _ in TILES];faces=[[]for _ in TILES]
    for j in range(bands):
        a=j/bands;d=(j+1)/bands;num=math.ceil(width/pitch)
        for i in range(-1,num+1):
            left=max(0,(i*pitch+(j%2)*pitch/2)/width)
            right=min(1,((i+1)*pitch+(j%2)*pitch/2)/width)
            if right-left<.005:continue
            color=((i*29+j*37+(i*j)%17)%13)//5
            shift=.0019 if lod else .0026
            def at(u,v,h):
                return (p+(q-p)*u)*(1-v)+(s+(r-s)*u)*v+normal*h
            points=[at(left+shift/width,a,.019),at(right-shift/width,a,.019),
                    at(right-shift/width,d-.00085,.005),at(left+shift/width,d-.00085,.005)]
            if np.cross(points[1]-points[0],points[2]-points[0])[2]<0:points=points[::-1]
            start=len(verts[color]);verts[color].extend(points);faces[color].append(tuple(start+k for k in range(4)))
    for color in range(3):b.add(verts[color],faces[color],TILES[color],label+'/staggered clay tile field')

def roof_y(b,x0,x1,y0,y1,ridge,eave,peak,lod,label):
    plane(b,[(x0,y0,eave),(x1,y0,eave),(x1,ridge,peak),(x0,ridge,peak)],lod,label+'/south pitch')
    plane(b,[(x1,y1,eave),(x0,y1,eave),(x0,ridge,peak),(x1,ridge,peak)],lod,label+'/north pitch')
    b.tube([(x0,ridge,peak+.023),(x1,ridge,peak+.023)],.073,TILES[0],6 if lod else 10,label+'/ridge')

def roof_x(b,x0,x1,y0,y1,ridge,eave,peak,lod,label):
    plane(b,[(x0,y1,eave),(x0,y0,eave),(ridge,y0,peak),(ridge,y1,peak)],lod,label+'/west pitch')
    plane(b,[(x1,y0,eave),(x1,y1,eave),(ridge,y1,peak),(ridge,y0,peak)],lod,label+'/east pitch')
    b.tube([(ridge,y0,peak+.023),(ridge,y1,peak+.023)],.071,TILES[0],6 if lod else 10,label+'/ridge')
    for q in [(x0,y0,eave),(x1,y0,eave)]:b.tube([q,(ridge,y0,peak+.03)],.074,EDGE,6 if lod else 9,label+'/painted bargeboards')

def chimney(b,x,y,foot,z,w=.78,d=.66):
    b.box((x,y,(foot+z)/2),(w,d,z-foot),BRICK,label='three roof chimneys/stacks')
    b.box((x,y,z-.10),(w+.19,d+.17,.18),CAP,label='three roof chimneys/corbelled heads')
    for o in (-.17,.17):
        b.box((x+o,y,z-.007),(w*.29,d*.67,.025),UNDER,label='three roof chimneys/flue mouths')

def make_roof(b,lod):
    roof_y(b,-6.00,16.58,4.61,13.82,9.46,6.76,10.67,lod,'long red ridge')
    roof_x(b,-5.69,1.84,3.87,10.14,-1.925,6.62,10.58,lod,'south cross gable')
    roof_y(b,-10.22,-5.29,-.57,6.01,2.53,3.14,5.38,lod,'west single-storey wing')
    chimney(b,-5.30,5.35,5.7,10.77,.78,.71)
    chimney(b,-.78,11.91,7.05,10.98,.84,.64)
    chimney(b,9.08,10.57,8.61,11.74,.64,.64)
