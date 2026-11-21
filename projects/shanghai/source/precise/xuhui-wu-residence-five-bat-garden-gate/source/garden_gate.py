"""Garden ceremonial gate behind the Wu Residence, from the two 2018 photographs."""
from math import cos, sin, pi
from shapely.geometry import Polygon, LineString, Point, box
from shapely.ops import unary_union
from shapely.affinity import scale
from photo_architecture import Facade

PAL = {
    'warm plaster': ([.511, .470, .376], .94),
    'brown sandstone': ([.424, .361, .279], .90),
    'carved pale stone': ([.607, .544, .430], .89),
    'bronze brown stone': ([.323, .252, .170], .94),
    'honey stone': ([.527, .422, .305], .88),
    'carved eave beam': ([.292, .238, .173], .90),
    'tile bed': ([.091, .148, .125], .92),
    'green glazed roll': ([.113, .225, .168], .54),
    'green glazed ridge': ([.179, .277, .201], .61),
}
PALETTE = {k: {'color':c, 'roughness':r} for k,(c,r) in PAL.items()}
RADIUS = .61
SPRING = 1.96
GATE_DEPTH = .54


def semicircle(radius, steps):
    return [(radius*cos(pi*i/steps), SPRING+radius*sin(pi*i/steps)) for i in range(steps+1)]


def ribbon(points, thickness):
    return LineString(points).buffer(thickness/2, cap_style=2, join_style=2)


def face_arch(face, detail):
    steps = 56 if detail else 24
    arc = semicircle(RADIUS, steps)
    aperture = Polygon([(-RADIUS, -.02), (RADIUS, -.02), *arc])
    outer = Polygon([(-.855,-.02),(.855,-.02),*semicircle(.855,steps)])
    face.prism(box(-1.52,0,1.52,3.59).difference(outer), -GATE_DEPTH, 0,
               'warm plaster', 'rendered gate wall')
    face.prism(outer.difference(aperture), -GATE_DEPTH, .019, 'honey stone', 'cut opening and jambs')
    a = Polygon([(-.835,-.02),(.835,-.02),*semicircle(.835,steps)])
    b = Polygon([(-.646,-.02),(.646,-.02),*semicircle(.646,steps)])
    face.prism(a.difference(b), .018, .038, 'brown sandstone', 'arch carving bed')
    for radius in (.637,.849):
        rim = semicircle(radius, steps)
        face.prism(ribbon([(radius,.425),*rim,(-radius,.425)], .018),.018,.052,
                   'carved pale stone','narrow stone fillet')
    for side in (-1,1):
        face.box(side*.755,.215,.313,.43,.646,-.24,'brown sandstone','plain pier foot')
        face.box(side*.75,.443,.293,.042,.603,-.236,'carved pale stone','foot moulding')

    def plane(u,v,theta):
        return ((.74+v)*cos(theta)-u*sin(theta), SPRING+(.74+v)*sin(theta)+u*cos(theta))

    # Each front cartouche has a crest and two separately cut inward-curling scrolls.
    steps_scroll=22 if detail else 12
    for i in range(9):
        theta=(i+.5)*pi/9
        parts=[]
        for side in (-1,1):
            line=[]
            for j in range(steps_scroll+1):
                t=j/steps_scroll
                rad=.060*(1-t)+.009*t
                a=pi*(.49+2.03*t)
                line.append(plane(side*(.062+rad*cos(a)), -.014+rad*sin(a),theta))
            parts.append(ribbon(line,.019 if detail else .023))
        crest=[(-.117,.021),(-.096,.064),(-.056,.070),(0,.092),(.058,.069),(.098,.063),(.118,.022)]
        parts.append(ribbon([plane(u,v,theta) for u,v in crest],.018))
        face.prism(unary_union(parts), .036, .061,'carved pale stone','paired cloud scroll %02d'%(i+1))
    return face


def bat_soffit(builder, detail):
    # Outstretched wing outline measured in the enlarged upward photograph.
    # Five winged reliefs follow the soffit from one spring point to the other.
    wing=[(.009,.087),(.051,.101),(.091,.084),(.151,.070),(.202,.025),(.208,-.014),
          (.175,.006),(.151,-.019),(.128,-.016),(.111,-.051),(.080,-.046),
          (.057,-.078),(.020,-.050),(.010,-.079)]
    center=[(-.024,.049),(-.031,.088),(-.009,.074),(.009,.074),(.031,.088),(.024,.049),
            (.036,.019),(.023,-.030),(0,-.097),(-.023,-.030),(-.035,.019)]
    silhouette=unary_union([Polygon(center),Polygon(wing),Polygon([(-u,v) for u,v in wing])])
    for i,angle in enumerate((.17,.88,pi/2,pi-.88,pi-.17)):
        # Wrap u (along the intrados) and v (through the opening) around the curve.
        def surface(u,v,d):
            a=angle+u/RADIUS
            radius=RADIUS+.004-d
            return (radius*cos(a),GATE_DEPTH*.50+v,SPRING+radius*sin(a))
        # u cross v in this parameterization points toward the center of the opening.
        builder.prism(silhouette,0,.027,surface,'honey stone','soffit/bat %d wings'%(i+1))
        body = scale(Point(0,-.009).buffer(1,quad_segs=9 if detail else 5),.026,.077,origin=(0,-.009))
        head = scale(Point(0,.065).buffer(1,quad_segs=8 if detail else 5),.026,.028,origin=(0,.065))
        builder.prism(unary_union([body,head]),.022,.045,surface,'honey stone','soffit/bat %d head and body'%(i+1))
        details=[ribbon([(side*.025,.033),(side*.083,.057),(side*.138,.033),(side*.172,.016)],.010)
                 for side in (-1,1)]
        if detail:
            details.extend(ribbon([(side*.040,.023),(side*.080,-.018),(side*.107,-.038)],.009)
                           for side in (-1,1))
        builder.prism(unary_union(details),.026,.039,surface,'carved pale stone','soffit/bat %d veins'%(i+1))


def coping(builder,face,detail):
    # Horizontal fret, corbels and upturned eaves remain separate editable groups.
    for z,h,thick,mat in [(3.61,.105,.69,'brown sandstone'),(3.74,.17,.70,'carved eave beam'),
                           (3.866,.07,.76,'honey stone'),(4.07,.14,.87,'carved eave beam')]:
        face.box(0,z,3.20,h,thick,-GATE_DEPTH/2,mat,'eave courses')
    for i in range(13):
        x=(i-6)*.235
        motif=[(-.108,.041),(.085,.041),(.085,-.043),(-.061,-.043),(-.061,.014),(.027,.014),(.027,-.016)]
        face.prism(ribbon([(x+u,3.745+v) for u,v in motif],.014),.075,.091,'honey stone','fret band')
    for x in (-1.36,-.67,0,.67,1.36):
        for z,w,th in [(3.927,.075,.37),(3.977,.13,.42),(4.02,.18,.46)]:
            face.box(x,z,w,.06,th,.02,'brown sandstone','stone corbel')

    def turn(x):
        return .205*(max(abs(x)-1.27,0)/.68)**1.75
    def height(x,t):
        return 4.172+.625*(t**1.25)+turn(x)
    n=25 if detail else 13
    for side in (-1,1):
        verts=[]
        for j in range(n+1):
            x=-1.95+3.90*j/n
            for k in range(5):
                t=k/4
                verts.append((x,.27+side*.82*(1-t),height(x,t)))
        quads=[]
        for j in range(n):
            for k in range(4):
                a=j*5+k
                q=[a,a+5,a+6,a+1]
                quads.append(q if side<0 else q[::-1])
        builder.add(verts,quads,'tile bed','roof/swept tile bed')
        # Convex half-round caps and the exposed circular rolled eave ends.
        for j in range(19):
            x=(j-9)*.205
            verts=[]
            faces=[]
            segments=7 if detail else 4
            for k in range(5):
                t=k/4
                for m in range(segments+1):
                    a=pi*m/segments
                    dx=.057*cos(a)
                    verts.append((x+dx,.27+side*.834*(1-t),height(x+dx,t)+.007+.073*sin(a)))
            for k in range(4):
                for m in range(segments):
                    a=k*(segments+1)+m
                    q=[a,a+1,a+segments+2,a+segments+1]
                    faces.append(q[::-1] if side<0 else q)
            end=list(range(segments+1))
            faces.append(end if side<0 else end[::-1])
            builder.add(verts,faces,'green glazed roll','roof/capped tile rows')
    # Pale ridge tile has a carved running scroll. Its upturned ends frame a
    # matched pair of fish-bodied dragons facing toward the ridge center.
    for k,sgn in enumerate((-1,1)):
        specimen=[(.00,.016),(.075,.047),(.155,.082),(.246,.049),(.346,.100),
                  (.384,.164),(.370,.215),(.310,.248),(.282,.306),(.237,.293),
                  (.198,.287),(.166,.246),(.181,.224),(.218,.229),(.213,.201),
                  (.180,.195),(.145,.218),(.100,.252),(.048,.249),(.068,.206),
                  (.095,.175),(.082,.139),(.047,.102),(-.032,.059)]
        base=1.64; anchor=height(base,1)+.065
        localdef=lambda pt: (sgn*(base-pt[0]),anchor+pt[1])
        fig=Polygon([localdef(p)for p in specimen])
        face.prism(fig,-.349,-.180,'brown sandstone','ridge end/fish dragon %d'%(k+1))
        face.prism(ribbon([localdef(p)for p in [(.030,.050),(.13,.098),(.222,.068),(.302,.104),(.342,.149)]],.016),
                   -.182,-.159,'carved pale stone','ridge end/body tracing')
    for j in range(16):
        x=(j-7.5)*.165
        pts=[(x+.058*cos(t*pi/12)*(.25+.75*t/24),height(x,1)+.073+.026*sin(t*pi/12)*(.25+.75*t/24)) for t in range(25)]
        face.prism(ribbon(pts,.009),-.183,-.168,'carved pale stone','ridge/running scroll')
    vertices=[]
    for j in range(n+1):
        x=-1.87+3.74*j/n
        for y,z in [(-.09,0),(-.066,.095),(0,.125),(.066,.095),(.09,0)]:
            vertices.append((x,.27+y,height(x,1)+z))
    geom=[]
    for j in range(n):
        for k in range(4):
            a=j*5+k
            geom.append([a,a+5,a+6,a+1])
    builder.add(vertices,geom,'brown sandstone','roof/raised ridge cap')


def add_building(builder,lod=False):
    face=Facade(builder,(-1.52,0),(1.52,0),'garden gate')
    face_arch(face,not lod)
    bat_soffit(builder,not lod)
    coping(builder,face,not lod)
