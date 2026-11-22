"""Model the courtyard-facing gable and the lower canted bay visible in 2015 and 2018."""
from math import cos, radians, sin
from pathlib import Path

from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from sign_lettering import lettering_shapes

PALETTE = {
    'warm cream render': {'color': [.69, .655, .54], 'roughness': .94},
    'shadowed reveal': {'color': [.49, .47, .40], 'roughness': .90},
    'dark painted timber': {'color': [.095, .064, .053], 'roughness': .79},
    'bargeboard shadow': {'color': [.062, .040, .037], 'roughness': .83},
    'gray verge cap': {'color': [.49, .50, .47], 'roughness': .82},
    'muted red clay': {'color': [.38, .205, .168], 'roughness': .90},
    'tile joint': {'color': [.425, .266, .231], 'roughness': .91},
    'warm white sash': {'color': [.72, .75, .715], 'roughness': .61},
    'casement glass': {'color': [.32, .39, .385], 'roughness': .31, 'metallic': .14},
    'transom glass': {'color': [.258, .307, .286], 'roughness': .34},
    'sill edging': {'color': [.119, .085, .061], 'roughness': .79},
    'base stone': {'color': [.52, .47, .38], 'roughness': .92},
    'mortar joint': {'color': [.19, .17, .134], 'roughness': .94},
    'bay cap': {'color': [.119, .088, .066], 'roughness': .72},
    'basement opening': {'color': [.135, .152, .139], 'roughness': .91},
    'plaque brass': {'color': [.66, .465, .172], 'roughness': .54, 'metallic': .26},
    'plaque edge': {'color': [.50, .371, .182], 'roughness': .50, 'metallic': .33},
    'plaque ink': {'color': [.164, .134, .096], 'roughness': .85},
}
WIDTH = 6.22
HALF = WIDTH / 2
WALL_EAVE = 9.42
APEX = 12.74
TIE = 8.73
PLINTH = 1.77
BAY_PATH = [(-.14, 0), (.23, -.32), (.69, -.85), (2.16, -.85),
            (2.86, -.54), (3.46, -.10), (3.77, .41), (3.77, .79), (3.11, 1.05)]
FONT = Path(__file__).parent / 'fonts' / 'LiuCourtyardSign.otf'


def strip(points, width):
    return LineString(points).buffer(width / 2, cap_style=2, join_style=2)


def sash(face, shape, name, split=False, transom=False, trim=False):
    x0, z0, x1, z1 = shape.bounds
    inside = shape.buffer(-.045, join_style=2)
    bars = []
    if split:
        mid = (x0 + x1) / 2
        bars.append(box(mid - .033, z0, mid + .033, z1))
    if transom:
        high = z0 + (z1-z0)*.704
        bars.append(box(x0, high-.030, x1, high+.030))
        face.prism(box(x0 + .014, high, x1 - .014, z1 - .012), -.149, -.141,
                   'transom glass', name + ' fanlight glazing')
    grid = shape.difference(inside.difference(unary_union(bars)))
    face.prism(shape, -.183, -.158, 'casement glass', name + ' glazing')
    face.prism(grid, -.113, -.059, 'warm white sash', name + ' sash')
    if trim:
        face.box((x0+x1)/2, z0-.041, x1-x0+.10, .076, .145, .039,
                 'sill edging', name + ' sill')


def ground_stone(face, bottom, top, left, right, label, lod, vent=False):
    """Incise the joints by allowing the recessed mortar bed to show through."""
    outline = box(left, bottom, right, top)
    opening = box(-.19, .235, .21, .435) if vent else None
    if vent:
        outline = outline.difference(opening)
        face.prism(opening, -.171, -.148, 'basement opening', label + ' vent recess')
    face.prism(outline, -.19, -.018, 'mortar joint', label + ' backing')
    course = (top-bottom)/5
    for row in range(5):
        z0, z1 = bottom + course*row, bottom+course*(row+1)
        step = .71 if not lod else .72
        start = left - ((.34 if row%2 else .04) + step)
        stones = []
        while start < right:
            end = start+step
            if end>left:
                lo, hi = max(start+.009,left), min(end-.009,right)
                if hi>lo:
                    slab = box(lo, z0+.008, hi, z1-.008).intersection(outline)
                    if not slab.is_empty:
                        stones.append(slab)
            start = end
        if stones:
            face.prism(unary_union(stones), -.025, .006,'base stone',label+' course '+str(row+1))


def fascia(f, lod):
    """Taper each photographed vertical post into the pitched external verge."""
    outline = Polygon([(-HALF,TIE),(HALF,TIE),(HALF,WALL_EAVE),
                       (0,APEX),(-HALF,WALL_EAVE)])
    attic = box(-.51,10.02,.51,11.04)
    timber = []
    # The photo shows four uprights beyond the pair immediately framing the attic on each side.
    for x, width in [(-2.94,.145),(-2.39,.14),(-1.84,.145),(-1.24,.17),(-.58,.177),
                     (0,.134),(.58,.175),(1.24,.165),(1.82,.14),(2.39,.14),(2.94,.14)]:
        high = 10.04 if x == 0 else APEX - abs(x)*(APEX-WALL_EAVE)/HALF
        piece=box(x-width/2,TIE-.02,x+width/2,high+.14).intersection(outline)
        # The middle uprights below the sill and in the dark lintel end cleanly at the glazing.
        timber.append(piece.difference(attic))
    timber.extend([box(-.67,9.91,.67,10.05),box(-.67,11.035,.67,11.17)])
    f.prism(unary_union(timber),.009,.105,'dark painted timber','attic studwork and lintels')
    f.box(0,TIE,WIDTH+.11,.19,.15,.054,'dark painted timber','gable tie beam')
    f.box(0,TIE-.101,WIDTH+.10,.052,.125,.042,'bargeboard shadow','tie lower mould')
    for x in (-2.85,2.82):
        f.box(x,TIE-.218,.156,.27,.13,.039,'dark painted timber','tie end block')
    for side in (-1,1):
        end=(side*3.52,9.22)
        ridge=(0,APEX+.055)
        for dz,depth,w,mat,name in [(-.065,.19,.186,'dark painted timber','verge board'),
                                    (-.177,.145,.052,'bargeboard shadow','verge underside'),
                                    (.083,.22,.096,'gray verge cap','verge cap')]:
            f.prism(strip([(end[0],end[1]+dz),(0,ridge[1]+dz)],w),-.52,depth,mat,name+str(side))
        roof=strip([(end[0],end[1]+.115),(0,ridge[1]+.115)],.068)
        f.prism(roof,-1.57,-.48,'muted red clay','visible roof return '+str(side))
        intervals=12 if lod else 22
        for j in range(1,intervals):
            u=j/intervals
            x=end[0]*(1-u);z=end[1]*(1-u)+ridge[1]*u+.154
            f.prism(strip([(x-.011*side,z+.012),(x+.011*side,z-.012)],.027),
                    -1.566,-.485,'tile joint','tile joints '+str(side))
        if not lod:
            for y in (.76,1.21):
                f.prism(strip([(end[0],end[1]+.15),(0,ridge[1]+.15)],.026),
                        -y-.015,-y+.015,'tile joint','tile laps '+str(side))
    sash(f,attic,'attic casement',split=True)


def plaque(face,lod):
    """The 2015 company plaque is in the solid central panel between the two glazed turns."""
    z = 2.52
    outer = box(-.396,z-.267,.396,z+.267)
    inner = outer.buffer(-.020,join_style=2)
    face.prism(outer,.008,.029,'plaque edge','2015 plaque support')
    face.prism(inner,.028,.034,'plaque brass','2015 plaque brass field')
    face.prism(outer.difference(inner),.029,.045,'plaque edge','2015 plaque rim')
    title = '上海华山康健医疗有限公司'
    for j,(ch,shape) in enumerate(lettering_shapes(title,.64,.057,font=FONT)):
        x0,_,x1,_ = shape.bounds
        u=(x0+x1)/2
        shape=affinity.rotate(shape, -u*60,origin=(u,0))
        shape=affinity.translate(shape,yoff=z+.075+.066*(1-(u/.31)**2))
        face.prism(shape.simplify(.00040 if lod else .00016),.0341,.0367,
                   'plaque ink','plaque title '+str(j+1))
    if not lod:
        text='Shanghai Huashan Health Development Co., Ltd'
        for idx,(_,item) in enumerate(lettering_shapes(text,.639,.029,font=FONT)):
            face.prism(affinity.translate(item.simplify(.00013),yoff=z-.075),.0341,.036,
                       'plaque ink','plaque English baseline')


def bay(builder,lod):
    plan=Polygon(BAY_PATH+[(BAY_PATH[0][0],1.05)])
    for idx,(a,b) in enumerate(zip(BAY_PATH,BAY_PATH[1:])):
        face=Facade(builder,a,b,'bay '+str(idx+1));half=face.length/2
        center=(idx==2)
        ground_stone(face,0,PLINTH,-half,half,'plinth',lod,vent=center)
        skin=box(-half,PLINTH,half,4.185)
        if idx in (1,3,4,5):
            opening=box(-half+.059,PLINTH+.038,half-.064,4.13)
            face.prism(skin.difference(opening),-.20,0,'warm cream render','jambs')
            sash(face,opening,'canted casement',transom=True)
        else:
            face.prism(skin,-.20,0,'warm cream render','solid panel')
        if center:plaque(face,lod)
    for bottom,top,projection,mat,label in [(PLINTH-.008,PLINTH+.041,.047,'sill edging','stone top weathering'),
                 (4.18,4.247,.043,'bay cap','bay cornice lower'),(4.245,4.331,.094,'bay cap','bay cornice bead'),
                 (4.33,4.42,.166,'dark painted timber','bay cornice fascia'),(4.421,4.468,.196,'bay cap','bay roof lip')]:
        builder.plan_prism(plan.buffer(projection,join_style=2),bottom,top,mat,label)


def add_gable(builder,lod=False):
    front=Facade(builder,(-HALF,0),(HALF,0),'courtyard')
    outline=Polygon([(-HALF,PLINTH),(HALF,PLINTH),(HALF,WALL_EAVE),
                     (0,APEX),(-HALF,WALL_EAVE)])
    openings=[(-1.54,6.59,-.51,8.25),(.52,6.59,1.59,8.25),(-2.09,1.90,-1.055,3.99)]
    holes=[box(*bounds) for bounds in openings]+[box(-.51,10.02,.51,11.04)]
    skin=outline.difference(unary_union(holes+[box(-.14,PLINTH,HALF,4.18)]))
    front.prism(skin,-.25,-.016,'shadowed reveal','wall substrate')
    front.prism(skin,-.016,.007,'warm cream render','courtyard render')
    ground_stone(front,0,PLINTH,-HALF,-.14,'wall plinth',lod)
    for i,name in enumerate(['western upper pair','eastern upper pair','lower casement']):
        sash(front,holes[i],name,split=True,transom=(i==2),trim=(i==2))
    front.box(.022,6.521,3.42,.119,.19,.066,'sill edging','paired upper sill')
    front.box((-HALF-.14)/2,PLINTH+.02,HALF-.14,.064,.10,.024,'sill edging','plinth top')
    for side in (-1,1):
        start=(side*HALF,0);end=(side*HALF,1.42)
        if side<0:start,end=end,start
        side_face=Facade(builder,start,end,'east end' if side>0 else 'west end')
        side_face.prism(box(-.71,PLINTH,.71,WALL_EAVE),-.18,0,'warm cream render','short wall return')
    fascia(front,lod)
    bay(builder,lod)
