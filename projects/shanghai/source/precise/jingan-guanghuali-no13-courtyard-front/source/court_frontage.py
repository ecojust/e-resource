"""No.13 gateposts, numbered enamel plate and adjacent photographed court wall."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon,box as rect
from shapely.geometry.polygon import orient
HERE=Path(__file__).resolve().parent
DETAIL=json.loads((HERE.parent/'measurements/courtyard-pier-observations.json').read_text())['summary']
BRICK='No13 | ochre facing brick'
LIME='No13 | warm white cornice'
STONE='No13 | grey plinth stone'
ENAMEL='No13 | green enamel'
TYPE='No13 | ivory number and road'
IRON='No13 | charcoal fittings'
def finish(rgb,rough=.83,metal=0.):
    linear=[((c/255+.055)/1.055)**2.4 if c>10 else c/255/12.92 for c in rgb]
    return dict(color=linear,roughness=rough,metallic=metal)
PALETTE={BRICK:finish((192,130,100)),LIME:finish((198,193,185)),STONE:finish((148,148,148)),
         ENAMEL:finish((41,79,64),.46,.12),TYPE:finish((210,205,165)),IRON:finish((63,61,62),.65,.35)}
def box(b,x0,x1,y0,y1,z0,z1,m,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=label)
def mould(b,xmid,ymid,sections,m,label):
    """One closed rectangular moulding with a consistent counterclockwise vertex loop."""
    vertices=[]
    for z,width,depth in sections:
        vertices.extend((xmid+dx*width/2,ymid+dy*depth/2,z)for dx,dy in [(-1,-1),(1,-1),(1,1),(-1,1)])
    last=len(vertices)-4;faces=[(3,2,1,0),tuple(range(last,last+4))]
    for i in range(0,last,4):
        for j in range(4):
            k=(j+1)%4;faces.append((i+j,i+k,i+k+4,i+j+4))
    b.add(vertices,faces,m,label)
def front_plate(b,shape,y0,y1,m,label):
    b.prism(orient(shape,sign=1),-y1,-y0,lambda x,z,d:(x,-d,z),m,label)
def number_plate(b,lod):
    xmin,xmax=DETAIL['number_plate_x'];zmin,zmax=DETAIL['number_plate_z'];y=.023
    shape=rect(xmin+.008,zmin+.008,xmax-.008,zmax-.008).buffer(.008,quad_segs=4,join_style=1)
    front_plate(b,shape,y-.007,y+.006,ENAMEL,'No13 | enamel address plate')
    info=json.loads((HERE.parent/'measurements/number-plate-letters.json').read_bytes())
    for char,polys in info['letters'].items():
        for outline in polys:
            def ring(coords):return [(xmin+x*(xmax-xmin),zmax-v*(zmax-zmin))for x,v in coords]
            area=Polygon(ring(outline['shell']),[ring(h)for h in outline['holes']])
            if area.is_valid and area.area>1e-10:
                front_plate(b,area,y-.0085,y-.006,TYPE,'Address plate | '+char)
    for i,(x,z) in enumerate([(xmin+.009,zmax-.012),(xmax-.009,zmin+.012)]):
        b.tube([(x,y-.007,z),(x,y-.010,z)],.0025,IRON,8,'Address plate | fixed stud '+str(i+1))
def add_courtyard(b,lod=False):
    b.palette.update(PALETTE)
    for key,(lo,hi) in [('left',DETAIL['left_shaft_x']),('right',DETAIL['right_shaft_x'])]:
        cx=(lo+hi)/2;w=hi-lo;cy=.226
        label='Court '+key+' pier | '
        mould(b,cx,cy,[(.005,w+.083,.495),(.336,w+.083,.495),(.392,w+.06,.472),(.444,w,.398)],STONE,label+'stone foot and shoulder')
        box(b,lo,hi,.027,.425,.442,1.981,BRICK,label+'facing brick shaft')
        mould(b,cx,cy,[(1.977,w,.398),(1.997,w+.018,.416),(2.014,w+.045,.443),(2.047,w+.10,.498),(2.067,w+.134,.532),(2.081,w+.166,.564),(2.119,w+.166,.564),(2.142,w+.141,.539)],LIME,label+'stepped concrete coping')
        box(b,lo+.005,hi-.005,.028,.424,2.139,2.286,LIME,label+'raised rectangular head')
    for lo,hi,side in [(-6.49,DETAIL['left_shaft_x'][0],'left'),(DETAIL['right_shaft_x'][1],2.325,'right')]:
        tag='Court '+side+' wall | '
        box(b,lo,hi,.153,.413,.017,.387,STONE,tag+'plinth')
        box(b,lo,hi,.161,.408,.379,1.573,BRICK,tag+'brick field')
        box(b,lo,hi,.145,.419,1.559,1.609,LIME,tag+'lower fascia bead')
        box(b,lo,hi,.153,.412,1.604,2.008,LIME,tag+'wide rendered fascia')
        box(b,lo,hi,.125,.44,1.996,2.049,LIME,tag+'shadow line')
        mould(b,(lo+hi)/2,.282,[(2.045,hi-lo,.306),(2.071,hi-lo,.346),(2.11,hi-lo,.346)],LIME,tag+'sloping weather cap')
    number_plate(b,lod)
