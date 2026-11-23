"""Opaque and glazed infills in the garden wall and on the street elevation."""
import math
from shapely.geometry import box
from residence_materials import GLASS,GREEN,IRON,LIGHT,SHADE


def glazing(f,bounds,name,cols=2,rows=3):
    hole=box(*bounds)
    x0,z0,x1,z1=bounds
    f.solid(hole,-.149,-.126,SHADE,name+' | frame bed')
    clear=hole.buffer(-.040,join_style=2)
    f.solid(hole.difference(clear),-.122,-.054,LIGHT,name+' | fixed perimeter')
    f.solid(clear,-.116,-.103,GLASS,name+' | dark glass')
    for j in range(1,cols):
        x=x0+(x1-x0)*j/cols
        width=.033 if cols==4 and j==2 else .013
        f.rect(x-width/2,x+width/2,z0+.03,z1-.03,-.105,-.057,GREEN,name+' | glazing bars')
    for j in range(1,rows):
        z=z0+(z1-z0)*j/rows
        f.rect(x0+.03,x1-.03,z-.009,z+.009,-.107,-.065,GREEN,name+' | glazing bars')


def louvre_leaf(f,l,h,width,height,lod,label):
    frame=box(l,h,l+width,h+height)
    inner=frame.buffer(-.047,join_style=2)
    f.solid(frame.difference(inner),.005,.048,GREEN,label+' | shutter frame')
    count=max(3,round(height/(.125 if lod else .080)))
    for i in range(count):
        bottom,top=h+.05+i*(height-.10)/count,h+.05+(i+1)*(height-.10)/count
        # Each blade is pitched outwards and has a shadow gap to the next.
        blade=box(l+.044,bottom,l+width-.044,top-.006)
        f.b.prism(blade,0,.017,lambda x,z,t:f.point(x,-.012-(top-z)*.39-t,z),GREEN,label+' | overlapping shutter blades')


def shutters(f,bounds,name,lod,angles):
    glazing(f,bounds,name,4,3)
    x0,z0,x1,z1=bounds
    for i,a in enumerate(angles):
        hinge=x0+.024 if i==0 else x1-.024
        angle=math.radians(a);sgn=1 if i==0 else -1
        # A face's local depth points inward. Negative depth opens into the garden.
        face=f.face(hinge,-.059,math.cos(angle),-sgn*math.sin(angle))
        width=(x1-x0)/2-.032
        louvre_leaf(face,0 if i==0 else -width,z0+.023,width,z1-z0-.046,lod,name)
        if not lod:
            for z in [z0+.18,z1-.18]:
                f.rail([(hinge,-.074,z-.028),(hinge,-.074,z+.028)],.014,IRON,name+' | shutter pin',8)
