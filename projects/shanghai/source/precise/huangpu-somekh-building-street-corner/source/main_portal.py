"""Beijing East Road entrance of the Somekh Building.

Portal dimensions are estimated from the restoration team's detail photograph,
restoration drawing and archival view. Local u is horizontal along the facade,
z is height and positive d projects out onto Beijing East Road.
"""
from functools import lru_cache
from math import cos, pi, sin
from pathlib import Path
from sign_lettering import lettering_shapes
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

GRANITE = 'Somekh warm grey granite'
WEATHER = 'Somekh granite joint shade'
ARRIS = 'Somekh dressed granite rim'
RENDER = 'Somekh warm grey facade backing'
STONE = 'Somekh worn granite threshold'
FRAME = 'Somekh grey green joinery'
GLASS = 'Somekh shaded glass'
PANEL = 'Somekh inset door panels'
IRON = 'Somekh dark fenestration metal'
BRONZE = 'Somekh muted bronze hardware'
LETTER = 'Somekh silver metal lintel lettering'
SIGN = 'THE SOMEKH BUILDING'
FONT = Path(__file__).parent/'fascia_font'/'SomekhFasciaStudy.otf'
PORTAL_MATERIALS = {
    LETTER: {'color': [.315, .349, .362], 'roughness': .33, 'metallic': .72},
    GRANITE: {'color': [.551, .505, .433], 'roughness': .88},
    WEATHER: {'color': [.365, .339, .287], 'roughness': .93},
    ARRIS: {'color': [.660, .615, .536], 'roughness': .81},
    RENDER: {'color': [.609, .579, .51], 'roughness': .90},
    STONE: {'color': [.446, .421, .375], 'roughness': .88},
    FRAME: {'color': [.229, .258, .238], 'roughness': .61},
    GLASS: {'color': [.142, .184, .191], 'metallic': .15, 'roughness': .27},
    PANEL: {'color': [.158, .180, .161], 'roughness': .70},
    IRON: {'color': [.183, .191, .182], 'metallic': .41, 'roughness': .58},
    BRONZE: {'color': [.404, .32, .208], 'metallic': .51, 'roughness': .56},
}

SPRING = 5.25
RAD_X = 1.235
RAD_Z = .87
DOOR_HALF = 1.075
DOOR_HEAD = 3.25


def _arch(x, z, rx, rz, steps):
    return [(x+rx*cos(pi*i/steps), z+rz*sin(pi*i/steps)) for i in range(steps+1)]


def _fan(center, steps):
    return Polygon([(center-RAD_X,4.88),(center+RAD_X,4.88)] +
                   _arch(center,SPRING,RAD_X,RAD_Z,steps))


def _box(face,x,z0,z1,width,back,front,material,label):
    face.box(x,(z0+z1)/2,width,z1-z0,front-back,(front+back)/2,material,label)


def _ring(face,poly,thickness,back,front,material,label):
    face.prism(poly.difference(poly.buffer(-thickness,join_style=2)),
               back,front,material,label)


def _pose_column(face,x,lod):
    # A Tuscan shaft is plain and tapers towards the neck. Keep the small torus,
    # neck fillet and abacus separate from the projecting horizontal entablature.
    _box(face,x,.085,.34,.611,-.035,.562,GRANITE,'Square plinths')
    _box(face,x,.346,.419,.628,-.044,.582,ARRIS,'Plinth rims')
    xy=face.point(x,0,.280)
    profile=[(.411,.259),(.452,.286),(.486,.283),(.521,.245),(.555,.238),
             (.598,.214),(.675,.207),(1.12,.211),(1.84,.203),(2.62,.189),
             (3.00,.179),(3.052,.182),(3.072,.208),(3.112,.209),
             (3.135,.183),(3.176,.188),(3.202,.216),(3.251,.253),(3.277,.254)]
    face.builder.lathe(tuple(xy[:2]),profile,GRANITE,12 if lod else 24,'Somekh Tuscan granite shafts')
    _box(face,x,3.272,3.353,.59,-.011,.566,ARRIS,'Column abaci')
    _box(face,x,3.346,3.397,.647,-.023,.589,GRANITE,'Column top plates')


def _leaf(face,x,z,angle,height,width,d,lod,label):
    poly=Polygon([(0.,0.),(-width*.43,height*.20),(-width*.5,height*.43),
                  (-width*.36,height*.68),(0.,height),(width*.37,height*.63),
                  (width*.49,height*.41),(width*.29,height*.16)])
    if lod:poly=poly.simplify(.018,preserve_topology=True)
    leaf=affinity.translate(affinity.rotate(poly,angle,origin=(0,0)),x,z)
    face.prism(leaf,d,d+.052,ARRIS,label)


def _bezier(controls,steps):
    a,b,c,d=controls
    return [tuple((1-t)**3*a[k]+3*(1-t)**2*t*b[k]+3*(1-t)*t*t*c[k]+t**3*d[k]
                  for k in (0,1)) for t in (i/steps for i in range(steps+1))]



@lru_cache(maxsize=2)
def _letters(lod):
    tolerance=.0018 if lod else .00075
    return [(char,outline.simplify(tolerance,preserve_topology=True))
            for char,outline in lettering_shapes(SIGN,2.11,.145,font=FONT)]


def _pediment(face,center,lod):
    rows=[(3.34,3.42,3.71,.01,.48,GRANITE),(3.415,3.472,3.88,.0,.575,ARRIS),
          (3.472,3.815,3.59,.03,.407,GRANITE),(3.816,3.895,3.91,.00,.550,ARRIS),
          (3.895,3.976,4.07,-.023,.596,GRANITE),(3.972,4.043,4.35,-.055,.654,ARRIS)]
    for a,b,width,back,f,mat in rows:_box(face,center,a,b,width,back,f,mat,'Portal architrave and projecting cornice')
    # The lettering can be read in the later close photograph as well as in
    # the restoration team's front detail. Retain the hotel logo as a separate
    # contemporary use in the source notes, away from the architectural lintel.
    _box(face,center,3.557,3.737,2.67,.395,.424,GRANITE,'Lintel inscription bed')
    for char,outline in _letters(lod):
        glyph=affinity.translate(outline,xoff=center,yoff=3.647)
        face.prism(glyph.buffer(.0032,join_style=2),.421,.445,IRON,'Metal letter sides')
        face.prism(glyph,.444,.454,LETTER,'Raised lintel letters '+char)
    for station in (-1.61,-1.07,-.54,0.,.54,1.07,1.61):
        _box(face,center+station,3.819,3.907,.15,.40,.586,GRANITE,'Dentils under the broken pediment')
    for side in (-1,1):
        def across(points):return [(center+side*x,z)for x,z in points]
        n=9 if lod else 24
        outer=_bezier([(2.13,4.033),(1.54,4.067),(1.25,4.69),(.84,4.765)],n)
        outer+=_bezier([outer[-1],(.60,4.815),(.46,4.711),(.485,4.557)],n)[1:]
        # Solid granite spandrel underneath the S-shaped broken pediment.
        belly=[(.56,4.40),(.72,4.34),(1.05,4.43),(1.50,4.20),(1.87,4.05)]
        face.prism(Polygon(across(outer+belly)),.16,.472,GRANITE,'Broken pediment granite spandrels')
        course=LineString(across(outer)).buffer(.063,quad_segs=4,cap_style=2,join_style=1)
        face.prism(course,.19,.544,ARRIS,'Volute moulded upper edges')
        run=_bezier([(1.98,4.053),(1.38,4.18),(1.08,4.63),(.817,4.652)],n)
        face.prism(LineString(across(run)).buffer(.022,quad_segs=3,cap_style=2),.454,.518,
                   WEATHER,'Inner pediment shadow lines')
        cx,cz=.698,4.559
        spiral=[]
        for k in range(n+1):
            t=k/n;radius=.216*(1-t)+.018*t;angle=pi*(.98+2.33*t)
            spiral.append((cx+radius*cos(angle),cz+radius*sin(angle)))
        face.prism(LineString(across(spiral)).buffer(.042 if lod else .033,quad_segs=4),
                   .45,.552,ARRIS,'Inward rolled volutes')
        for x,z,ang in [(.17,4.087,-38),(.29,4.15,-54),(.39,4.20,-60)]:
            _leaf(face,center+side*x,z,ang*side,.30,.16,.405,lod,'Carved cartouche leaves')
    medallion=affinity.scale(Point(center,4.28).buffer(1,quad_segs=6 if lod else 12),
                             xfact=.202,yfact=.24,origin=(center,4.28))
    face.prism(medallion,.337,.465,GRANITE,'Central oval cartouche')
    _ring(face,medallion,.040,.45,.52,ARRIS,'Cartouche edge')
    _leaf(face,center,4.45,0,.25,.20,.385,lod,'Cartouche crown')



def _hanging_carvings(face,center,lod):
    # Paired drops flank the open pediment below the archivolt in the repair
    # drawing. Model the relief outline where the photograph shows stone.
    for side in (-1,1):
        x=center+side*1.53
        _box(face,x,4.15,4.86,.055,.022,.095,WEATHER,'Pendulum carving stems')
        for z,scale in [(4.20,.64),(4.47,.78),(4.75,.89)]:
            poly=Point(x,z).buffer(.080*scale,quad_segs=3 if lod else 6)
            face.prism(poly,.057,.143,GRANITE,'Stone pendant flower hearts')
            for angle in (-49,0,49):
                _leaf(face,x,z+.011,angle,.135*scale,.094*scale,.074,lod,'Pendant flower leaves')
            tip=Polygon([(x-.049*scale,z-.025),(x+.049*scale,z-.025),(x,z-.128*scale)])
            face.prism(tip,.064,.121,ARRIS,'Pendant drop tips')



def _garlands(face,center,lod):
    # The high-resolution close view shows two shallow stone swags above the
    # fanlight. Its upright keystone interrupts them before they meet.
    for side in (-1,1):
        line=[(center+side*a,6.395-.274*sin(pi*(a-.19)/1.47))
              for a in [.19+1.47*i/16 for i in range(17)]]
        face.prism(LineString(line).buffer(.038,quad_segs=3,cap_style=2),
                   .017,.139,GRANITE,'Garland undercut cords')
        for i in range(9 if not lod else 5):
            t=(i+.5)/(9 if not lod else 5);x=.19+1.47*t;z=6.397-.274*sin(pi*t)
            for leafside in (-1,1):
                _leaf(face,center+side*x,z-.062,leafside*54,.15+.04*sin(pi*t),
                      .082 if not lod else .11,.105,lod,'Carved swag leaves')
        x=center+side*1.74
        for ang in (-68,0,68):
            _leaf(face,x,6.31,ang,.15,.10,.113,lod,'Stone bow terminals')
        for z in [6.18,5.99]:
            face.prism(Point(x,z).buffer(.056,quad_segs=3 if lod else 6),
                       .032,.135,GRANITE,'Small pendant bosses')


def _upper_window(face,center,window,lod):
    face.prism(window.buffer(.012,join_style=2),-.322,-.302,GLASS,'Semicircular transom glass')
    _ring(face,window,.072,-.266,-.135,FRAME,'Arched transom frame')
    region=window.buffer(-.068,join_style=2)
    frame=[]
    for dx in (-.785,-.393,0.,.393,.785):
        frame.append(box(center+dx-.027,4.92,center+dx+.027,5.48))
    for z in [5.18,5.47]:
        frame.append(box(center-RAD_X,z-.024,center+RAD_X,z+.024))
    # The lower panes have straight muntins. The crown has radiating bars rising
    # from the rail, inside the same shallow elliptical arched frame.
    origin=(center,5.46)
    for angle in (pi/6,pi/3,pi/2,2*pi/3,5*pi/6):
        frame.append(LineString([origin,(center+1.35*cos(angle),5.46+.82*sin(angle))]).buffer(.018,cap_style=2))
    face.prism(unary_union(frame).intersection(region),-.23,-.145,IRON,'Radial and straight transom bars')
    face.box(center,4.87,2.65,.10,.28,.036,ARRIS,'Granite fanlight sill')
    # Each voussoir has its own recessed joint. The apex keystone projects forward.
    segments=11 if lod else 15
    for i in range(segments):
        a=pi*i/segments+.004;b=pi*(i+1)/segments-.004
        points=[]
        for radius_x,radius_z,angles in [(RAD_X+.075,RAD_Z+.075,[a,(a+b)/2,b]),
                 (RAD_X+.454,RAD_Z+.320,[b,(a+b)/2,a])]:
            points.extend([(center+radius_x*cos(t),SPRING+radius_z*sin(t))for t in angles])
        face.prism(Polygon(points),-.026,.185 if i!=segments//2 else .243,
                   GRANITE if i%3 else ARRIS,'Jointed granite fanlight voussoirs')
    key=Polygon([(center-.114,6.043),(center+.114,6.043),(center+.185,6.475),(center-.185,6.475)])
    face.prism(key,.115,.274,ARRIS,'Crown keystone')
    for side in (-1,1):
        _box(face,center+side*(RAD_X+.096),4.91,5.255,.22,-.09,.165,GRANITE,'Fanlight jamb stones')
        _box(face,center+side*(RAD_X+.234),5.175,5.262,.49,-.074,.216,ARRIS,'Fanlight springing imposts')


def _door(face,center,door,lod):
    x0,z0,x1,z1=door.bounds
    face.prism(door.buffer(.012,join_style=2),-.722,-.700,GLASS,'Recessed door glazing')
    gate=door.buffer(-.038,join_style=2);leaf_fields=[];moulds=[]
    for side in (-1,1):
        x=center+side*.511
        bottom=box(x-.397,.24,x+.397,1.371);top=box(x-.397,1.57,x+.397,2.89)
        leaf_fields.extend([bottom,top])
        face.prism(bottom,-.671,-.650,PANEL,'Inset lower door panels')
        moulds.append(bottom.difference(bottom.buffer(-.054,join_style=2)))
        face.prism(top,-.686,-.661,GLASS,'Six lights in each door leaf')
        bars=[box(x-.023,1.57,x+.023,2.89)]
        for z in (2.01,2.45):bars.append(box(x-.399,z-.021,x+.399,z+.021))
        face.prism(unary_union(bars).intersection(top),-.638,-.600,FRAME,'Upper door light muntins')
        face.line((center+side*.112,1.318,-.516),(center+side*.112,1.61,-.516),
                  .018 if lod else .016,BRONZE,6,'Door pull bars')
    face.prism(gate.difference(unary_union(leaf_fields)),-.656,-.584,FRAME,'Double door rails and stiles')
    for side in (-1,1):
        header=box(center+side*.5-.405,3.035,center+side*.5+.405,3.197)
        face.prism(header,-.590,-.555,PANEL,'Recessed rectangular door head panels')
        _ring(face,header,.022,-.557,-.534,FRAME,'Door head panel moulding')
    face.prism(unary_union(moulds),-.635,-.574,FRAME,'Door panel raised beads')
    for side in (-1,1):
        _box(face,center+side*1.167,.085,3.264,.18,-.66,-.036,GRANITE,'Stone-lined door jambs')
    _box(face,center,3.215,3.299,2.39,-.67,.03,ARRIS,'Door opening head')
    for i,(front,top)in enumerate([(.67,.078),(.445,.152),(.205,.227)]):
        _box(face,center,.016+i*.025,top,2.44,-.698,front,STONE,'Entrance granite steps')


def add_portal(face,center,lod=False):
    """Fill a 4.20 m by 6.48 m rectangular host opening around the main entrance."""
    steps=12 if lod else 30
    window=_fan(center,steps)
    door=box(center-DOOR_HALF,.04,center+DOOR_HALF,DOOR_HEAD)
    backing=box(center-2.10,0.,center+2.10,6.48)
    skin=backing.difference(door.union(window))
    face.prism(skin,-.52,-.069,WEATHER,'Punched masonry backing')
    # The restoration drawing shows horizontal stucco joints at both sides of the
    # stone frame. End these courses at the host wall interfaces.
    for i in range(13):
        z0=i*.50+.014;z1=min(6.481,(i+1)*.50-.019)
        stone=skin.intersection(box(center-2.10,z0,center+2.10,z1))
        if not stone.is_empty:face.prism(stone,-.07,.013,RENDER,'Incised side wall courses')
    _door(face,center,door,lod)
    for side in (-1,1):_pose_column(face,center+side*1.55,lod)
    _pediment(face,center,lod)
    _hanging_carvings(face,center,lod)
    _upper_window(face,center,window,lod)
    _garlands(face,center,lod)
