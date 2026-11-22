"""Attributed reconstruction of the surviving inscribed entrance panel at Lane 1032.

Glyph centre lines are newly drawn from the three historical characters and the
legible enamel street plate. Coordinates below run downward on a 10-unit grid.
"""
import random
from math import hypot
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union

def finish(rgb, roughness=.85, metallic=0):
    def linear(channel):
        v=channel/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return dict(color=[linear(c) for c in rgb],roughness=roughness,metallic=metallic)

PALETTE={
    'pebble render':finish((141,141,132)), 'letter field':finish((176,167,140)),
    'limestone chip':finish((183,183,170)), 'granite chip':finish((84,84,80)),
    'gilded relief':finish((206,176,81),.51,.39),'plate enamel':finish((39,113,85),.47,.20),
    'enamel white':finish((228,227,207),.55),'plate rim':finish((89,100,87),.55,.26),
    'aged screw':finish((110,109,91),.57,.34)
}
# Visible left-to-right order on the historical stone reads 村 山 岐.
INSCRIPTION=[
    [[(3.2,.4),(3.5,2.2),(3.1,6.6),(3.2,9.6)],[(.3,3.8),(2.5,3.1),(5.2,2.9)],[(3.1,3.5),(1.6,5.8),(.2,7.4)],[(3.3,4.5),(4.6,5.5),(5,5.9)],[(4.7,3.3),(7.2,2.8),(9.9,2.8)],[(7.2,.4),(7.8,1.2),(7.6,6.4),(7.7,9.1),(7.1,9.4),(5.9,8.4)],[(5.4,4.7),(5.9,5.6),(6.4,5.8)]],
    [[(.8,3.0),(1.1,5.4),(1.1,8.6),(2.7,8.0),(5.9,7.3),(9.1,7.6)],[(4.7,.4),(5.2,1.8),(5.05,7.4)],[(9.1,3.7),(9.2,5.3),(9.0,9.0)]],
    [[(.9,3.5),(.9,6.8),(1.6,6.2),(2.8,5.7)],[(2.1,.7),(2.3,2.0),(2.1,5.8)],[(3.9,2.8),(3.8,4.7),(3.2,6.1)],[(4.7,3.0),(6.2,2.7),(9.1,2.3)],[(6.8,.35),(7.1,1.4),(6.9,4.3)],[(4.5,4.8),(6.1,4.6),(8.1,4.4),(7.4,5.8),(5.7,7.4),(3.4,8.5),(2.1,8.6)],[(4.7,5.6),(6.1,6.6),(7.8,7.8),(9.7,9.0)]]
]
# Independent line lettering for the contemporary address plate. No typeface
# outline or photograph is embedded in the geometry.
SIGNS={
'0':[[(2,1),(6,1),(8,3),(8,7),(6,9),(3,9),(1,7),(1,3),(2,1)]],
'1':[[(2,3),(5,1),(5,9)],[(2,9),(8,9)]],
'2':[[(1,3),(2,1),(6,1),(8,3),(8,4),(1,9),(8,9)]],
'3':[[(1,1),(7,1),(8,3),(6,5),(3,5)],[(6,5),(8,6),(8,8),(6,9),(1,9)]],
'4':[[(7,9),(7,1),(1,7),(9,7)]],
'8':[[(3,1),(6,1),(8,3),(7,4),(3,6),(1,7),(2,9),(6,9),(8,7),(7,6),(2,4),(1,3),(3,1)]],
'–':[[(1,5),(8,5)]],
'弄':[[(1,1),(9,1)],[(5,1),(5,5)],[(2,3),(8,3)],[(1,5),(9,5)],[(1,7),(9,7)],[(4,6),(4,7),(3,9)],[(7,6),(7,9)]],
'号':[[(3,1),(8,1),(8,4),(3,4),(3,1)],[(1,5),(9,5)],[(4,5),(3,7),(8,7),(7,9),(5,9)]],
'愚':[[(2,1),(8,1),(8,4),(2,4),(2,1)],[(3,2.5),(7,2.5)],[(5,1),(5,6)],[(1,7),(1,5),(9,5),(9,7)],[(2,8),(1,9)],[(3,7.5),(4,9),(7,9)],[(5,7),(6,8)],[(8,7.8),(9,9)]],
'园':[[(1,1),(9,1),(9,9),(1,9),(1,1)],[(3,3),(7,3)],[(2,5),(8,5)],[(4,5),(3,7)],[(6,5),(6,7),(8,7)]],
'路':[[(.5,1),(4,1),(4,4),(.5,4),(.5,1)],[(2.5,4),(2.5,8)],[(2.5,6),(4,6)],[(.5,5),(.5,9),(4,8)],[(6,1),(5,4)],[(6,2),(9,2),(8,4),(5,6)],[(6,3),(9.5,6)],[(5.5,6.5),(9,6.5),(9,9),(5.5,9),(5.5,6.5)]]
}

def brush(points,scale,left,top,lod):
    nodes=[(left+x*scale,top-y*scale) for x,y in points]
    segments=[]
    for i,((x,z),(u,v)) in enumerate(zip(nodes,nodes[1:])):
        dx,dz=u-x,v-z;length=hypot(dx,dz)
        nx,nz=-dz/length,dx/length
        a=scale*(.32 if i==0 else .48); b=scale*(.23 if i==len(nodes)-2 else .48)
        segments.append(Polygon([(x+nx*a,z+nz*a),(u+nx*b,v+nz*b),(u-nx*b,v-nz*b),(x-nx*a,z-nz*a)]))
    segments.extend(Point(x,z).buffer(scale*.48,quad_segs=2 if lod else 5) for x,z in nodes[1:-1])
    return unary_union(segments)
def add_building(b,lod=False):
    def face(name,shape,front,back,mat):
        b.prism(shape,-back,-front,lambda x,z,d:(x,-d,z),mat,name)
    field=box(-.545,.229,.545,.736)
    face('pier stonework around recessed lettering',box(-.84,0,.84,1.075).difference(field),0,.26,'pebble render')
    face('recessed inscription bed',field,.027,.26,'letter field')
    rng=random.Random(1032)
    for i in range(260 if lod else 1250):
        x=rng.uniform(-.834,.834);z=rng.uniform(.006,1.068)
        if field.contains(Point(x,z)) or (-.43<x<.43 and .76<z<1.072):continue
        r=rng.uniform(.002,.0075)
        face('aggregate '+str(i%4),Polygon([(x-r,z),(x,z+r*.7),(x+r,z-r*.7)]),-.0007,.0004,
             'limestone chip' if i%2 else 'granite chip')
    for i,paths in enumerate(INSCRIPTION):
        glyph=unary_union([brush(line,.0336,-.532+i*.355,.665,lod) for line in paths])
        face(['left village character','centre mountain character','right Qi character'][i],glyph,.008,.029,'gilded relief')
    face('enameled address plate rim',box(-.366,.778,.366,1.035),-.017,.007,'plate rim')
    face('green enamel address plaque',box(-.355,.788,.355,1.024),-.021,-.015,'plate enamel')
    for x in (-.338,.338):
        for z in (.802,1.010):
            face('corner fastening',Point(x,z).buffer(.006,quad_segs=4 if lod else 9),-.025,-.019,'aged screw')
    for text,top,advance,scale in [('1032弄1–148号',.988,.059,.0060),('愚园路',.856,.139,.0051)]:
        for i,symbol in enumerate(text):
            origin=-(len(text)-1)*advance*.5+i*advance-4.5*scale
            outline=unary_union([LineString([(origin+u*scale,top-v*scale) for u,v in line]).buffer(scale*.53,quad_segs=1 if lod else 3) for line in SIGNS[symbol]])
            face('plate '+str(i)+' '+symbol,outline,-.023,-.0208,'enamel white')
