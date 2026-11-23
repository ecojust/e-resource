"""Outer masonry, occupied street windows and photographed residential fittings.

The four roof vertices are the measured footprint. Positive depth is into the
housing. The east face and the hidden parts of the returns retain the envelope.
"""
from pathlib import Path
import json
from math import cos, sin, pi
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

from courtyard import B, C, G, I, Bay, mat

SOURCE = Path(__file__).resolve().parent
STEEL = 'Street | painted iron casements'
WHITE = 'Street | replacement enamel sash'
GLASS = 'Street | grey daylight glazing'
GREEN = 'Street | green sheet metal'
BLUE = 'Street | blue canvas'
MORTAR = 'Street | warm pale cornice'
SILL = 'Street | sill stone'
PIPES = 'Street | pale pipework'
AC = 'Street | aged condenser casing'
VENT = 'Street | recessed grille'
SHOP = 'Street | grey shop render'
MASONRY_HEAD = 'Street | rubbed brick window head'
PALETTE = {
    STEEL: mat((61,63,54),.65), WHITE: mat((197,194,174),.62),
    GLASS: mat((102,119,115),.38), GREEN: mat((65,92,71),.74),
    BLUE: mat((50,78,111),.78), MORTAR: mat((174,163,137),.96),
    SILL: mat((126,124,108)), PIPES: mat((189,182,152)),
    AC: mat((184,178,154)), VENT: mat((76,78,68),.62),
    SHOP: mat((154,152,134)), MASONRY_HEAD: mat((130,70,49))
}


def dimensions(axis, level, storey):
    settings = axis | axis.get('overrides', {}).get(str(level), {})
    bottom = level * storey + settings.get('sill', .78)
    return axis['x'], settings['width'], bottom, bottom + settings.get('height', 2.13)


def sash(wall, axis, level, storey, lod):
    x, width, bottom, top = dimensions(axis,level,storey)
    code = axis.get('rooms', {}).get(str(level), '')
    tag = f"axis {axis['id']} floor {level+1}"
    frame = WHITE if 'W' in code else STEEL
    rebate = .135
    wall.box(x, rebate+.045, (bottom+top)/2, width-.012, .042, top-bottom-.014, GLASS, tag+' pane')
    for side in [-1,1]:
        wall.box(x+side*(width/2-.027), rebate, (bottom+top)/2, .054,.085,top-bottom,frame,tag+' jamb')
    for z in [bottom+.030,top-.030]:
        wall.box(x,rebate,z,width,.085,.060,frame,tag+' rail')
    cols = 3 if 'T' in code else 2
    for i in range(1,cols):
        wall.box(x-width/2+i*width/cols,rebate-.012,(bottom+top)/2,.042,.072,top-bottom,frame,tag+' mullion')
    rows = [.68] if frame==WHITE else ([.35,.68] if lod else [.24,.46,.68,.84])
    for frac in rows:
        wall.box(x,rebate-.005,bottom+(top-bottom)*frac,width-.065,.057,.031,frame,tag+' transom')
    wall.box(x,-.024,bottom-.042,width+.18,.31,.085,SILL,tag+' sill')
    if 'P' in code:
        # Light infill occupies the head of two bays on the north return.
        wall.box(x,.045,top+.22,width,.12,.44,MORTAR,tag+' blocked upper panel')
    if 'H' in code:
        head=Polygon([(x-width/2-.01,top+.01),(x+width/2+.01,top+.01),
                      (x+width/2+.15,top+.30),(x-width/2-.15,top+.30)])
        wall.surface(head,-.018,.012,MASONRY_HEAD,tag+' splayed brick lintel')
    if 'A' in code:
        condenser(wall,x,bottom,width,tag,lod)
    if 'R' in code or 'G' in code or 'C' in code or 'B' in code:
        canopy(wall,x,width,top,tag,code,lod)
    if 'K' in code:
        security_grille(wall,x,width,bottom,top,tag,lod)
    if 'D' in code:
        drying_rails(wall,x,width,bottom,tag,lod)


def condenser(wall,x,sill,width,tag,lod):
    # Boxes hang immediately below the opening on steel angle brackets.
    w = min(.79,width-.08)
    z = sill-.37
    wall.box(x,-.265,z,w,.38,.53,AC,tag+' condenser')
    cx=x-w*.11
    ring=Point(cx,z).buffer(.203,quad_segs=4 if lod else 7)
    wall.surface(ring,-.470,-.445,VENT,tag+' round condenser intake')
    if not lod:
        rim=ring.difference(Point(cx,z).buffer(.176,quad_segs=7))
        wall.surface(rim,-.483,-.465,AC,tag+' raised fan ring')
    if lod:
        return
    for i in range(5):
        dx=(i-2)*.067
        bar_height=2*(.17**2-dx**2)**.5
        wall.box(cx+dx,-.481,z,.015,.015,bar_height,AC,tag+' condenser grille')
    for side in [-1,1]:
        u=x+side*w*.37
        wall.tube((u,-.04,z-.49),(u,-.40,z-.29),.017,I,tag+' condenser bracket',6)


def canopy(wall,x,width,top,tag,code,lod):
    reach=.51 if 'C' in code else .69
    w=width+.24
    z=top+.10
    if 'R' not in code:
        color=BLUE if 'B' in code else GREEN if 'G' in code else STEEL
        if 'B' in code:
            segments=4 if lod else 9
            top_curve=[(-.035-reach*sin(pi*i/(2*segments)),z-.24+.26*cos(pi*i/(2*segments))) for i in range(segments+1)]
            profile=Polygon(top_curve+[(d,hei-.038) for d,hei in reversed(top_curve)])
        else:
            profile=Polygon([(-reach,z-.115),(-.03,z),(-.03,z+.046),(-reach,z-.064)])
        wall.section(profile,x-w/2,x+w/2,color,tag+' weather hood')
    for side in [-1,1]:
        s=x+side*w*.47
        wall.tube((s,-.02,z+.012),(s,-reach,z-.084),.019,I,tag+' cantilever',6)
        if not lod:
            wall.tube((s,-.03,z-.22),(s,-reach,z-.087),.014,I,tag+' hood brace',6)
    if 'R' in code:
        wall.tube((x-w*.47,-reach,z-.084),(x+w*.47,-reach,z-.084),.016,GREEN,tag+' drying frame',6)


def security_grille(wall,x,width,bottom,top,tag,lod):
    depth=.31
    h=top-bottom
    for s in [-1,1]:
        wall.box(x+s*(width/2+.035),-depth*.53,(top+bottom)/2,.034,depth,h,STEEL,tag+' cage side')
    for z in [bottom+.02,bottom+h*.55,top-.02]:
        wall.box(x,-depth,z,width+.12,.036,.029,STEEL,tag+' cage rail')
    n=5 if lod else 9
    for i in range(n):
        s=x-width/2+width*i/(n-1)
        wall.box(s,-depth,(top+bottom)/2,.018,.021,h,STEEL,tag+' cage bar')


def drying_rails(wall,x,width,z,tag,lod):
    reach=.56
    for side in [-1,1]:
        s=x+side*width*.47
        wall.tube((s,-.02,z+.06),(s,-reach,z+.04),.023,I,tag+' drying rack',6)
        if not lod:
            wall.tube((s,-.02,z-.35),(s,-reach,z+.04),.016,I,tag+' rack brace',5)
    for d in ([-reach] if lod else [-reach,-reach*.55]):
        wall.tube((x-width*.55,d,z+.05),(x+width*.55,d,z+.05),.018,I,tag+' drying rod',6)


def rainwater_pipe(wall,x,storey,lod):
    top=5*storey+1.4
    wall.tube((x,-.090,.18),(x,-.090,top-.13),.060,PIPES,'external rainwater downpipe',8 if lod else 12)
    wall.tube((x,-.090,top-.13),(x,-.19,top),.060,PIPES,'rainwater elbow',8)
    for level in range(1,5):
        z=level*storey+.35
        wall.box(x,-.085,z,.155,.155,.050,I,'pipe strap')


def cornice(wall,storey):
    roof=5*storey
    # A broad continuous rendered fascia masks the slab; its projecting top
    # lip follows the four independently mapped bearings.
    for z,h,d,m,label in [
        (roof+.66,1.60,.26,MORTAR,'deep rendered cornice'),
        (roof+1.59,.27,.37,MORTAR,'parapet'),
        (roof+1.78,.11,.43,SILL,'coping nosing')]:
        wall.box(wall.length/2,.035,z,wall.length,d,h,m,label)


def shops(wall,ranges,entrance,lod):
    """Recessed modern shop glass and shallow rendered fascias seen in 2018."""
    holes=[]
    for i,(a,b,kind) in enumerate(ranges):
        if entrance and not (b<entrance[0]-.21 or a>entrance[1]+.21):
            continue
        x=(a+b)/2
        width=b-a
        holes.append(box(a,.10,b,2.57))
        tag=f'shop {i+1}'
        wall.box(x,.14,1.335,width,.08,2.46,GLASS,tag+' front glazing')
        for s in [a+.035,x,b-.035]:
            wall.box(s,.079,1.335,.067,.081,2.46,STEEL,tag+' frame')
        wall.box(x,.065,2.14,width,.080,.058,STEEL,tag+' shop transom')
        wall.box(x,-.12,2.89,width+.20,.43,.51,SHOP,tag+' sign backing')
        wall.box(x,-.18,3.190,width+.25,.55,.09,SILL,tag+' fascia coping')
        if kind=='awning':
            profile=Polygon([(-.83,2.48),(-.14,2.66),(-.14,2.71),(-.83,2.54)])
            wall.section(profile,a,b,GREEN,tag+' awning')
            if not lod:
                for s in [a+.18,b-.18]:
                    wall.tube((s,-.13,2.32),(s,-.80,2.49),.018,I,tag+' awning bracket',6)
    return holes


def add_street(b,lod,layout):
    survey=json.loads((SOURCE/'street-fabric.json').read_text())
    corners=layout['outer_corners']
    h=layout['storey_pitch']
    public=layout.get('public_entrance') or {}
    for i,key in enumerate(['west','south','east','north']):
        wall=Bay(b,corners[i],corners[(i+1)%4],'Exterior '+key)
        face=survey[key]
        axes=face['axes']
        holes=[]
        entrance=None
        if key=='west' and 'outer_x' in public:
            x=public['outer_x']
            width=public.get('width',2.80)
            entrance=(x-width/2,x+width/2)
            holes.append(box(entrance[0],-.02,entrance[1],public.get('height',3.05)))
        for axis in axes:
            for level in axis['levels']:
                x,width,bot,top=dimensions(axis,level,h)
                holes.append(box(x-width/2,bot,x+width/2,top))
                sash(wall,axis,level,h,lod)
        holes.extend(shops(wall,face.get('shops',[]),entrance,lod))
        poly=box(0,0,wall.length,5*h+1.65).difference(unary_union(holes))
        wall.surface(poly,.0,.34,B,'perforated exterior masonry')
        for a in face.get('downpipes',[]):
            rainwater_pipe(wall,a,h,lod)
        cornice(wall,h)
    for cap in survey.get('north_roof_projections', []):
        base=Polygon(cap['outline_xy'])
        roof=5*h
        top=roof+cap['top_above_roof_deck']
        b.plan_prism(base,roof+.030,top,B,cap['id']+' red brick roof body')
        b.plan_prism(base.buffer(.070,join_style=2),top,top+.09,SILL,cap['id']+' thin coping')
        b.plan_prism(base.buffer(-.050,join_style=2),top+.09,top+.12,C,cap['id']+' flat roof')
