"""Materials, flat ironwork and relief lettering for the Qinyuan entrance."""
from math import cos, sin, pi
from pathlib import Path
from shapely import affinity
from shapely.geometry import LineString, Point
from sign_lettering import lettering_shapes

VIOLET='Violet bicycle notice'; IRON='Blackened structural iron'; EDGE='Worn black scrollwork'; RED='Vermilion enamel'
RETURN='Cream painted letter returns'; WOOD='Weathered oval timber'; GRAIN='Brown engraved lettering'
BRICK='Oxblood facing brick'; BURNT='Burnt red brick'; FADED='Faded red brick'
MORTAR='Pale recessed mortar'; STONE='Grey cement casing'; PANEL='Grey rendered plaque panel'
GREEN='Green enamel address plate'; WHITE='Warm ivory enamel'; INK='Dark inscription'
BRONZE='Graphite bronze memorial'; HIGHLIGHT='Weathered bronze relief'; ALLOY='Dull silver heritage plate'
FONT=Path(__file__).parent/'fonts/QinyuanGateSubset.otf'

def material(rgb, roughness=.85, metallic=0):
    s=[v/255 for v in rgb]
    return {'color':[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in s],
            'roughness':roughness,'metallic':metallic}

PALETTE={VIOLET:material((74,64,115),.65),IRON:material((42,45,42),.60,.38),EDGE:material((63,64,55),.62,.44),
         RED:material((159,62,62),.62),RETURN:material((167,137,128)),WOOD:material((118,99,76)),
         GRAIN:material((84,70,56)),BRICK:material((127,66,63)),BURNT:material((112,59,54)),
         FADED:material((139,77,68)),MORTAR:material((171,166,150)),STONE:material((156,154,146)),
         PANEL:material((170,170,160)),GREEN:material((46,100,84),.58),WHITE:material((215,211,182)),
         INK:material((71,72,62)),BRONZE:material((87,87,76),.72,.31),
         HIGHLIGHT:material((107,107,93),.66,.31),ALLOY:material((171,169,154),.60,.23)}

def strip(face, path, width, back, front, mat, label):
    shape=LineString(path).buffer(width/2,cap_style='flat',join_style='round',quad_segs=2)
    face.prism(shape,back,front,mat,label)

def oval(x,z,rx,rz,lod):
    return affinity.scale(Point(x,z).buffer(1,quad_segs=8 if lod else 15),rx,rz,origin=(x,z))

def letters(face, text, x,z, width,height, back,front, mat, label, lod=False, angle=0):
    for char, outline in lettering_shapes(text,width,height,font=FONT):
        tolerance=min(.0017 if lod else .0008, height*.008)
        shape=affinity.rotate(outline.simplify(tolerance,preserve_topology=True),angle,origin=(0,0))
        face.prism(affinity.translate(shape,x,z),back,front,mat,label+' '+char)

def scroll(face,cx,cz,rx,rz,direction,back,width,mat,label,lod,tilt=0,turns=.96):
    """A flat forged strip winds inward from the rail. Tilt follows the arch tangent."""
    count=11 if lod else 20
    a=tilt*pi/180
    path=[]
    for i in range(count+1):
        t=i/count
        phi=pi*(.91-2*turns*t)
        r=(1-.80*t)
        x=direction*r*rx*cos(phi);z=r*rz*sin(phi)
        path.append((cx+x*cos(a)-z*sin(a),cz+x*sin(a)+z*cos(a)))
    strip(face,path,width,back,back+.019,mat,label)
