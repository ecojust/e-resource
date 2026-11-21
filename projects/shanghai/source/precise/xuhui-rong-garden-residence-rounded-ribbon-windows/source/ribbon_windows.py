"""The two ribbon windows on the left wing as seen from the garden in October 2015."""
from math import cos, pi, sin
from pathlib import Path
from random import Random

from PIL import Image, ImageFilter
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

WALL = 'Pale warm roughcast'
CEMENT = 'Grey sand-finished concrete'
LIP = 'Light window reveal'
SOFFIT = 'Shaded cement underside'
STEEL = 'Charcoal steel casements'
PUTTY = 'Dark grey glazing bead'
GLASS = 'Grey-green garden glass'
GLASS_UP = 'Cool upper glazing'
SILL = 'Sill top'
PALETTE = {
    key: dict(color=color, roughness=roughness, metallic=metal)
    for key, color, roughness, metal in (
        (WALL,[.72,.735,.695],.97,0), (CEMENT,[.40,.38,.32],.93,0),
        (LIP,[.61,.57,.48],.94,0),(SOFFIT,[.32,.305,.265],.95,0),
        (SILL,[.47,.45,.41],.91,0), (STEEL,[.045,.054,.052],.58,.14),
        (PUTTY,[.115,.113,.097],.81,0), (GLASS,[.118,.147,.140],.29,.24),
        (GLASS_UP,[.145,.178,.173],.29,.24))
}
TANGENT = -1.45
BEND = .50
LEFT = TANGENT - BEND
RIGHT = 2.89
RETURN = 1.29
NOSE = 1.03
RADIUS = .625
OPENINGS = (.18,3.29)
TOP = 5.51
PIER = (.175,.405)

def make_texture(path):
    rng=Random(387)
    broad=Image.new('L',(45,43))
    broad.putdata([rng.randrange(218,227) for _ in range(45*43)])
    base=broad.resize((225,215),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(.6))
    image=Image.new('L',base.size)
    image.putdata([max(0,min(255,v+rng.randrange(-4,5))) for v in base.getdata()])
    image.convert('RGB').save(path)

def flat(b, poly, back, front, material, label):
    if not poly.is_empty:
        b.prism(poly,back,front,lambda x,z,d:(x,-d,z),material,label)

def height(b, poly, low, high, material, label):
    if not poly.is_empty:
        b.prism(poly,low,high,lambda x,y,z:(x,y,z),material,label)

def arc_xy(radius,start,end,count):
    return [(TANGENT+radius*cos(start+(end-start)*step/count),
             BEND+radius*sin(start+(end-start)*step/count))
            for step in range(count+1)]

def curved_wall(outer,inner,start=-pi,end=-pi/2,count=24):
    return Polygon(arc_xy(outer,start,end,count)+arc_xy(inner,end,start,count))

def aperture(bottom, radius, segments):
    zmid=bottom+RADIUS
    pts=[(TANGENT,zmid-radius)]
    for i in range(segments+1):
        a=-pi/2+i*pi/segments
        pts.append((NOSE+radius*cos(a),zmid+radius*sin(a)))
    pts.append((TANGENT,zmid+radius))
    return Polygon(pts)

def return_strip(width, inner=.115, end=RETURN, segments=24):
    front=box(TANGENT,-width,RIGHT,inner)
    corner=curved_wall(BEND+width,BEND-inner,count=segments)
    side=box(LEFT-width,BEND,LEFT+inner,end)
    return unary_union((front,corner,side))

def taper_hood(b, bottom, floor, count):
    """Carry the sunshade down the round jamb, tapering its projection to the plaster rim."""
    rings = []
    for i in range(count+1):
        angle = (pi/2) * (1-i/count)
        depth = .061 + .209*sin(angle)**1.7
        ring = []
        for radius, y in [(RADIUS+.011, -.048), (RADIUS+.083, -.048),
                          (RADIUS+.083, -depth), (RADIUS+.011, -depth)]:
            ring.append((NOSE+radius*cos(angle), y, bottom+RADIUS+radius*sin(angle)))
        rings.extend(ring)
    faces = []
    for i in range(count):
        for j in range(4):
            a=4*i+j
            c=4*i+(j+1)%4
            faces.append((a,c,c+4,a+4))
    faces.extend([(0,3,2,1), (4*count,4*count+1,4*count+2,4*count+3)])
    b.add(rings, faces, CEMENT, f'Level {floor} tapered rounded hood')

def front_window(b, floor, bot, segments, lod):
    label=f'Level {floor} '
    outer=aperture(bot,RADIUS,segments)
    edge=aperture(bot,RADIUS+.070,segments)
    flat(b,edge.difference(outer),-.016,.056,LIP,label+'rounded plaster facing')
    reveal=aperture(bot,RADIUS-.031,segments)
    flat(b,outer.difference(reveal),-.152,-.026,CEMENT,label+'cement reveal')
    flat(b,reveal,-.17,-.154,GLASS if floor==1 else GLASS_UP,label+'recessed dark panes')
    flat(b,box(PIER[0],bot,PIER[1],bot+RADIUS*2),-.160,-.006,WALL,label+'plastered solid mullion')
    visible=reveal.difference(box(PIER[0],bot-.1,PIER[1],bot+RADIUS*2+.1))
    inner=aperture(bot,RADIUS-.069,segments)
    flat(b,reveal.difference(inner).intersection(visible),-.143,-.092,STEEL,label+'curved steel perimeter')
    for i,x in enumerate((TANGENT+.12,-.87,-.30,.51,1.04,1.31)):
        steel=box(x-.018,bot,x+.018,bot+2*RADIUS).intersection(visible)
        flat(b,steel,-.145,-.083,STEEL,label+f'steel stile {i+1}')
    for i,fraction in enumerate((.25,.50,.75)):
        z=bot+2*RADIUS*fraction
        rail=box(TANGENT,z-.013,NOSE+RADIUS,z+.013).intersection(visible)
        flat(b,rail,-.151,-.106,STEEL,label+f'glazing bar {i+1}')
        if not lod:
            bead=box(TANGENT,z+.013,NOSE+RADIUS,z+.021).intersection(visible)
            flat(b,bead,-.151,-.131,PUTTY,label+f'glazing bead {i+1}')
    if not lod:
        thin=aperture(bot,RADIUS+.080,segments).difference(edge)
        flat(b,thin,-.008,.012,CEMENT,label+'fine outer edge')

def corner_window(b, floor, bot, lod):
    label=f'Level {floor} outside corner '
    top=bot+2*RADIUS
    # Three planar lights turn the corner under the continuous curved hood.
    glass=GLASS if floor==1 else GLASS_UP
    corners=3
    for j in range(corners):
        a0=-pi+j*pi/(2*corners);a1=a0+pi/(2*corners)
        piece=curved_wall(BEND-.154,BEND-.17,a0,a1,1)
        height(b,piece,bot+.03,top-.03,glass,label+f'faceted glazing {j+1}')
        for i,fraction in enumerate((.25,.5,.75)):
            z=bot+2*RADIUS*fraction
            height(b,curved_wall(BEND-.099,BEND-.15,a0,a1,1),z-.014,z+.014,
                   STEEL,label+f'glazing bar {j+1}.{i+1}')
    for j in range(corners+1):
        angle=-pi+j*pi/(2*corners)
        edge=curved_wall(BEND-.075,BEND-.156,angle-.024,angle+.024,1)
        height(b,edge,bot+.026,top-.026,STEEL,label+f'corner steel {j+1}')
    for i,z in enumerate((bot,top-.037)):
        height(b,curved_wall(BEND-.084,BEND-.153,count=3),z,z+.037,STEEL,label+f'perimeter rail {i+1}')
    side=box(LEFT+.154,BEND,LEFT+.17,RETURN)
    height(b,side,bot+.026,top-.026,glass,label+'short return glazing')
    for i,y in enumerate((BEND+.14, BEND+.50,RETURN-.018)):
        height(b,box(LEFT+.083,y-.018,LEFT+.153,y+.018),bot,top,STEEL,label+f'return stile {i+1}')
    for i,fraction in enumerate((.25,.50,.75)):
        z=bot+2*RADIUS*fraction
        height(b,box(LEFT+.101,BEND,LEFT+.15,RETURN),z-.014,z+.014,STEEL,label+f'return bar {i+1}')
    for i,z in enumerate((bot-.056,top)):
        lip=return_strip(.135 if i==0 else .270, inner=.18)
        lip=lip.intersection(box(LEFT-.35,-.35,NOSE+.012,RETURN+.012))
        height(b,lip,z,z+.056 if i==0 else z+.083,SILL if i==0 else CEMENT,label+('sill','overhanging shade')[i])
        if not lod and i==1:
            height(b,lip.buffer(-.011,join_style=2),z-.012,z,SOFFIT,label+'hood underside')

def add_building(b,lod):
    segments=14 if lod else 40
    holes=unary_union([aperture(bot,RADIUS,segments) for bot in OPENINGS])
    flat(b,box(TANGENT,0,RIGHT,TOP).difference(holes),-.19,0,WALL,'Garden front with two rounded openings')
    corner_band=curved_wall(BEND,BEND-.19,count=segments)
    corner_shell=unary_union((corner_band,box(LEFT,BEND,LEFT+.19,RETURN)))
    boundaries=[(0,OPENINGS[0]),(OPENINGS[0]+2*RADIUS,OPENINGS[1]),(OPENINGS[1]+2*RADIUS,TOP)]
    for i,(low,high) in enumerate(boundaries):
        height(b,corner_shell,low,high,WALL,f'Rounded external wall {i+1}')
    for j,bot in enumerate(OPENINGS,1):
        front_window(b,j,bot,segments,lod)
        corner_window(b,j,bot,lod)
        taper_hood(b,bot,j,14 if lod else 30)
    fascia=return_strip(.305,inner=.095,segments=segments)
    height(b,fascia,TOP-.48,TOP-.368,CEMENT,'Continuous upper concrete fascia')
    if not lod:
        height(b,fascia.buffer(-.014,join_style=2),TOP-.51,TOP-.48,SOFFIT,'Upper fascia underside')
    height(b,return_strip(.019,inner=.235,segments=segments),TOP-.017,TOP,LIP,'Low parapet cap')
    b.palette[WALL]['texture']=str(Path(__file__).with_name('roughcast.png'))
    for part in b.parts:
        if part['material']!=WALL:continue
        verts=part['vertices']
        part['texcoords']=[[(x-LEFT+y*.38)/(RIGHT-LEFT+.54),1.-z/TOP] for x,y,z in verts]
