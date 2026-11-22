"""Pale arched surround, recessed horizontal exhaust blades and adjacent facing brick."""
from math import pi,cos,sin,sqrt
from shapely.geometry import Polygon,box

WIDTH = 1.04
SLATS = 6
OPEN_RADIUS = .375
SPRING = .246
OPEN_RISE = .361
BASE = .177
BLADE_PITCH = .054
BRICK_W = .225
BRICK_H = .073
PALETTE = {
    'weathered pale surround': {'color':[.53,.493,.409],'roughness':.89},
    'worn rim': {'color':[.61,.564,.462],'roughness':.80},
    'shadowed masonry reveal': {'color':[.26,.241,.193],'roughness':.92},
    'dark louver face': {'color':[.024,.027,.029],'roughness':.77},
    'worn louver edge': {'color':[.045,.047,.048],'roughness':.78},
    'red facing brick': {'color':[.215,.066,.049],'roughness':.92},
    'deep fired brick': {'color':[.147,.056,.046],'roughness':.91},
    'sun-faded brick': {'color':[.31,.118,.082],'roughness':.90},
    'brick joint': {'color':[.115,.09,.077],'roughness':.98}
}

def outline(radius,spring,rise,bottom,segments):
    arc=[(radius*cos(pi*i/segments),spring+rise*sin(pi*i/segments)) for i in range(segments+1)]
    return Polygon([(-radius,bottom),(radius,bottom),*arc])

def extrude(b,shape,front,back,mat,name):
    if not shape.is_empty:
        b.prism(shape,-back,-front,lambda x,z,d:(x,-d,z),mat,name)

def half_open(z):
    if z<=SPRING:return OPEN_RADIUS
    return OPEN_RADIUS*sqrt(max(0,1-((z-SPRING)/OPEN_RISE)**2))

def blade(b,num):
    z=BASE+.015+BLADE_PITCH*num
    yz=[(.065,z),(.128,z+.031),(.131,z+.025),(.068,z-.006)]
    verts=[]
    for y,h in yz:
        hw=half_open(h)+.001
        verts.extend([(-hw,y,h),(hw,y,h)])
    # Wind outward: the lower front hem and upper face are distinguishable in the old photograph.
    name='Louver '+str(num+1)
    b.add(verts,[(0,1,3,2)],'dark louver face',name+' inclined slat')
    b.add(verts,[(2,3,5,4),(4,5,7,6),(6,7,1,0),(0,2,4,6),(1,7,5,3)],'worn louver edge',name+' hem and underside')

def add_vent(b,lod=False):
    n=18 if lod else 54
    outer=outline(WIDTH/2,.243,.493,.052,n)
    inner=outline(OPEN_RADIUS,SPRING,OPEN_RISE,BASE,n)
    inner_back=outline(OPEN_RADIUS-.012,SPRING,OPEN_RISE-.010,BASE+.009,n)
    field=box(-.72,0,.72,.84)
    # The back plate is perforated throughout the aperture. Real sightlines pass between blades.
    extrude(b,field.difference(outer),.015,.145,'brick joint','Lime joints surrounding the photographed vent')
    for row in range(12):
        z=row*BRICK_H+.003
        for col in range(-5,5):
            x=col*BRICK_W+row%2*BRICK_W/2
            fragment=box(x+.004,z,x+BRICK_W-.004,z+BRICK_H-.007).intersection(field).difference(outer)
            hue=('red facing brick','red facing brick','deep fired brick','sun-faded brick','red facing brick')[(row*7+col*3)%5]
            extrude(b,fragment,0,.014,hue,'Running bond course '+str(row+1))
    extrude(b,outer.difference(inner),-.015,.040,'weathered pale surround','Single pale arched surround and square sill')
    if not lod:
        # The old image shows a softly rounded arris under the light; three shallow courses keep it editable.
        for i in range(3):
            end=outer.buffer(-.0017*(i+1),join_style=1,quad_segs=2)
            cut=inner.buffer(.0017*(i+1),join_style=1,quad_segs=2)
            extrude(b,end.difference(cut),-.018-i*.002,-.015-i*.002,'worn rim','Rounded arris '+str(i+1))
    else:
        extrude(b,outer.buffer(-.005).difference(inner.buffer(.005)),-.022,-.015,'worn rim','Light arris')
    extrude(b,inner.difference(inner_back),.037,.14,'shadowed masonry reveal','Sloped inner reveal')
    for i in range(SLATS):blade(b,i)
