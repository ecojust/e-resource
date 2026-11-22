"""Build the three street-facing window axes and the returns of the projecting wings."""
from pathlib import Path
import json
from shapely.geometry import LineString, box
from shapely.ops import unary_union

from brickwork import texture_uv
from photo_architecture import Facade
from entrance_portico import PORTAL_MATERIALS, add_entrance

SOURCE = Path(__file__).resolve().parent
EDGES = json.loads((SOURCE/'frontage-registration.json').read_bytes())['visible_edges_local_m']
BRICK = 'Huqiu red brick'
PLASTER = 'pale street plaster'
STONE = 'grey cement moulding'
GLASS = 'blue grey street glass'
FRAME = 'dark slim steel frame'
SPANDREL = 'darker brick edging'
COPING = 'dark coping'
SILL = 'sill stone'
ROOF = 'patinated roof metal'
PALETTE = {
    name: {'color': value, 'roughness': roughness} for name, value, roughness in [
        (BRICK, [1,1,1], .90), (PLASTER, [.76,.74,.72], .81),
        (STONE, [.64,.62,.60], .80), (GLASS, [.34,.42,.45], .36),
        (FRAME, [.16,.18,.17], .60), (SPANDREL, [.51,.285,.28], .85),
        (COPING, [.26,.25,.24], .66), (SILL, [.49,.47,.44], .73),
        (ROOF, [.36,.38,.37], .78), ('attic painted trim',[.71,.68,.61],.75),
        ('window grille', [.20,.21,.21], .58),
    ]
}
PALETTE.update(PORTAL_MATERIALS)
PALETTE[BRICK]['texture'] = str(SOURCE/'huqiu-red-brick.png')
NAMES = ['south wing','south inward return','central recessed front','north inset return','north bevel','north wing']
UPPER_SILLS = (5.18,8.51,11.84,15.12)
BASE = 4.70
ROOF_LINE = 18.52


def window(face, opening, label, lod, *, high_transom=False, bars=False):
    x0,z0,x1,z1 = opening.bounds
    width,height = x1-x0,z1-z0
    # The glass closes the opening behind a real reveal. Put the horizontal
    # transom up in the sash, as visible in the 2014 street photograph.
    zt = z0+height*(.66 if high_transom else .74)
    pieces = [box(x0,zt-.025,x1,zt+.025)]
    if width > .82:
        x = (x0+x1)/2
        pieces.append(box(x-.025,z0,x+.025,z1))
    inner = opening.buffer(-.060,join_style='mitre')
    grid = opening.difference(inner.difference(unary_union(pieces)))
    face.prism(opening.buffer(.012,join_style='mitre'),-.29,-.26,GLASS,label+' glass')
    face.prism(grid,-.19,-.105,FRAME,label+' steel')
    if not lod:
        face.box((x0+x1)/2,z0-.04,width+.12,.085,.23,-.025,SILL,label+' sill')
    if bars:
        for j in range(7 if not lod else 5):
            count = 7 if not lod else 5
            x=x0+(j+1)*width/(count+1)
            face.box(x,(z0+z1)/2,.025,height,.046,.09,'window grille','street grilles')
        for h in (.18,.80):
            face.box((x0+x1)/2,z0+h*height,width,.033,.045,.105,'window grille','grille straps')


def ground_floor(face, index, lod):
    if index==2:
        aperture=box(-4.08,-.04,4.08,4.73)
        face.wall(0,4.73,[aperture],.52,PLASTER)
        # The 2014 street photograph shows continuous masonry behind the
        # entrance crest, up to the first row of upper windows.
        face.prism(box(-4.08,4.065,4.08,BASE),-.49,-.028,BRICK,'brick backing above the entrance')

        return
    count = 3 if index in (0,5) else 1
    inset = .50 if count==3 else .23
    step = (face.length-2*inset)/count
    rooms = []
    for j in range(count):
        center = -face.length/2+inset+(j+.5)*step
        width = step*(.70 if count==3 else .79)
        rooms.append(box(center-width/2, .88, center+width/2, 3.45))
    face.wall(0, BASE, rooms, .52, PLASTER)
    for hole in rooms:
        window(face,hole,'base window',lod,high_transom=True,bars=True)
    face.beam(.20,.40,.06,COPING,label='plinth')
    face.beam(4.27,.16,.11,STONE,label='top of plaster')
    face.beam(4.53,.22,.23,COPING,label='street string course')


def upper_windows(face, index, lod):
    count = 3 if index in (0,2,5) else 1
    # The narrow wall opposite the north return forms the deep side of the entry.
    # Short reveals remain individually readable instead of wrapping a flat texture over them.
    inset = .66 if count==3 else (.20 if face.length>2.15 else .15)
    step = (face.length-2*inset)/count
    xs = [-face.length/2+inset+(j+.5)*step for j in range(count)]
    width = min(step*.77,2.10 if count==1 else 1.82)
    holes = []
    for floor,z in enumerate(UPPER_SILLS):
        h = 2.08 if floor<3 else 1.75
        for x in xs:holes.append(box(x-width/2,z,x+width/2,z+h))
    face.wall(BASE,ROOF_LINE,holes,.54,BRICK)
    for floor,z in enumerate(UPPER_SILLS):
        for j,x in enumerate(xs):
            opening=holes[floor*count+j]
            window(face,opening,'upper sash',lod)
            if floor<3:
                # Recessed brick panels between floors are clearly visible at street level.
                panel_width=width*.94
                face.box(x,z-.49,panel_width,.76,.092,.021,BRICK,'spandrel panels')
                if not lod:
                    face.box(x,z-.88,panel_width+.10,.066,.11,.035,SPANDREL,'spandrel lower course')
        if floor==2 and count==3:
            for j in range(1,count):
                face.box((xs[j-1]+xs[j])/2,9.83,.32,9.74,.21,.070,BRICK,'shallow brick piers')
    for z,h,p,mat in [(14.60,.15,.14,STONE),(17.00,.16,.16,COPING),(17.36,.60,.12,PLASTER),
                       (17.72,.12,.10,STONE),(18.08,.55,.055,BRICK),(18.47,.12,.11,COPING)]:
        face.beam(z,h,p,mat,width=face.length,label='attic courses')


def top_storey(face,lod):
    # The north wing is one floor taller in both street photographs.
    a=face.point(-face.length/2+.12,0,-.42)[:2];b=face.point(face.length/2-.12,0,-.42)[:2]
    attic=Facade(face.builder,a,b,'north rooftop addition')
    widths=(.22,.23,.27);positions=(-.335,-.032,.29);apertures=[]
    for fraction,x in zip(widths,positions):
        half=attic.length*fraction/2;center=x*attic.length
        apertures.append(box(center-half,18.89,center+half,20.60))
    attic.wall(18.38,21.14,apertures,.38,'attic painted trim')
    for hole in apertures:window(attic,hole,'attic sash',lod)
    attic.beam(20.98,.15,.14,STONE,label='eaves')
    attic.beam(21.20,.14,.18,COPING,label='roof lip')
    for end in (-attic.length/2,attic.length/2):
        attic.box(end,19.86,.18,2.55,1.10,-.35,'attic painted trim','attic return')
    rim=LineString([a,b]).buffer(1.08,single_sided=True,join_style='mitre',cap_style='flat')
    face.builder.plan_prism(rim,21.09,21.19,ROOF,'north rooftop edge')


def add_building(builder,lod):
    for index,(a,b) in enumerate(zip(EDGES,EDGES[1:])):
        face=Facade(builder,a,b,NAMES[index])
        ground_floor(face,index,lod)
        upper_windows(face,index,lod)
        if index==5:top_storey(face,lod)
    add_entrance(builder,lod)
    ledge=LineString(EDGES).buffer(1.26,single_sided=True,join_style='mitre',cap_style='flat')
    builder.plan_prism(ledge,18.31,18.41,ROOF,'street edge behind the parapet')
    for part in builder.parts:
        if part['material']==BRICK:
            part['texcoords']=[(u,1-v)for u,v in (texture_uv(*vertex)for vertex in part['vertices'])]
