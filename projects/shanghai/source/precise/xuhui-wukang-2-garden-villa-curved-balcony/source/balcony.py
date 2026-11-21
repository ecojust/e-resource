"""Editable centre bay of the former Mo residence facing its private garden."""
from math import cos, pi, radians, sin
from shapely.geometry import Polygon

RADIUS, PROJECTION, REAR = 3.04, 2.60, 1.05
SHAFT_X, SHAFT_Y = 1.86, -1.68
SOFFIT, CURB, HANDRAIL = 3.34, 3.96, 4.95
PALETTE = {name: {'color': color, 'roughness': roughness} for name, color, roughness in [
    ('pale balcony render', [.72,.63,.47], .91),
    ('ivory column', [.76,.69,.55], .86),
    ('balcony floor', [.47,.43,.33], .94),
    ('porch wall', [.55,.43,.31], .96),
    ('bronze green circles', [.13,.247,.172], .64),
    ('green stretcher rails', [.096,.187,.126], .67),
    ('timber finish', [.112,.058,.032], .77),
    ('glazing in shade', [.056,.084,.067], .31),
    ('entry paving', [.36,.33,.286], .90),
    ('pendant bronze', [.17,.126,.065], .64),
    ('pendant glass', [.57,.52,.363], .41),
]}

def on_curve(angle, inset=0):
    return ((RADIUS-inset)*sin(angle), -(PROJECTION-inset)*cos(angle))

def plan(inset, segments):
    arc = [on_curve(-pi/2 + pi*i/segments, inset) for i in range(segments+1)]
    return Polygon([*arc, (RADIUS-inset, REAR), (-RADIUS+inset, REAR)])

def lip(inset, width, segments):
    arc = [-pi/2+pi*i/segments for i in range(segments+1)]
    return Polygon([*(on_curve(a,inset) for a in arc),
                    *((x,y) for x,y in [(RADIUS-inset,REAR),(RADIUS-inset-width,REAR)]),
                    *(on_curve(a,inset+width) for a in reversed(arc)),
                    (-RADIUS+inset+width,REAR),(-RADIUS+inset,REAR)])

def platform(b,lod):
    seg = 24 if lod else 80
    b.plan_prism(plan(.06,seg), SOFFIT, SOFFIT+.30, 'pale balcony render', 'curved balcony slab')
    b.plan_prism(lip(.018,.16,seg), SOFFIT+.178, SOFFIT+.238,'ivory column','projecting lower drip')
    b.plan_prism(lip(-.038,.22,seg), SOFFIT+.273, SOFFIT+.357,'ivory column','balcony nose')
    b.plan_prism(plan(.035,seg), SOFFIT+.30, SOFFIT+.373,'balcony floor','terrace surface')
    b.plan_prism(lip(.055,.17,seg), SOFFIT+.36, CURB,'pale balcony render','curved solid parapet foot')
    b.plan_prism(lip(.018,.231,seg), CURB-.063, CURB+.017,'ivory column','stone capping to curb')
    b.plan_prism(lip(.032,.206,seg), HANDRAIL-.124, HANDRAIL,'pale balcony render','curved ivory parapet cap')

def columns(b,lod):
    # The garden elevation resolves the taper, square neck abacus and plinth.
    # Foliage hides the lowest courses. Their heights are approximations.
    for sign,side in [(-1,'left'),(1,'right')]:
        x = sign*SHAFT_X
        b.box((x,SHAFT_Y,.082),(.59,.59,.164),'pale balcony render',label=side+' column square plinth')
        if lod:
            profile=[(.147,.274),(.226,.278),(.308,.230),(2.991,.192),(3.065,.222),(3.157,.265)]
        else:
            profile=[(.147,.270),(.180,.278),(.210,.279),(.239,.259),(.255,.239),
                     (.282,.252),(.308,.230),(.740,.226),(1.460,.217),(2.25,.206),
                     (2.94,.194),(2.984,.194),(3.004,.215),(3.028,.216),(3.045,.203),
                     (3.070,.214),(3.095,.233),(3.122,.256),(3.158,.271)]
        b.lathe((x,SHAFT_Y),profile,'ivory column',14 if lod else 40,side+' Tuscan column')
        b.box((x,SHAFT_Y,3.25),(.62,.61,.182),'ivory column',label=side+' capital abacus')
    for sign in (-1,1):
        x=sign*(RADIUS-.13)
        b.box((x,.255,1.67),(.29,.43,3.34),'pale balcony render',label='wall end pilaster')
        b.box((x,.245,3.105),(.36,.47,.12),'ivory column',label='return pilaster band')

def railing(b,lod):
    breaks=[-pi/2, radians(-36), radians(36), pi/2]
    for i,a in enumerate(breaks):
        x,y=on_curve(a,.13)
        radial=(sin(a),-cos(a),0)
        tangent=(cos(a),sin(a),0)
        axes=(tangent,radial,(0,0,1))
        b.box((x,y,(HANDRAIL+CURB)/2),(.295,.20,HANDRAIL-CURB),'pale balcony render',
              basis=axes,label='stone railing division '+str(i+1))
    for i,(a,beta) in enumerate(zip(breaks,breaks[1:])):
        count = 6 if i==1 else 5
        a+=.056
        beta-=.056
        for z in (4.052,4.77):
            path=[(*on_curve(a+(beta-a)*k/14,.135),z) for k in range(15)]
            b.tube(path,.031,'green stretcher rails',6 if lod else 10,'balustrade horizontal bars')
        pitch=(beta-a)/count
        for j in range(count):
            mid=a+(j+.5)*pitch
            n=12 if lod else 30
            # Each open oval follows the round balcony, even at the returns.
            points=[(*on_curve(mid+.396*pitch*cos(2*pi*k/n),.135),4.414+.333*sin(2*pi*k/n))
                    for k in range(n+1)]
            b.tube(points,.048,'bronze green circles',5 if lod else 8,'linked upright oval')
            if j:
                boundary=mid-.5*pitch
                p=on_curve(boundary,.135)
                b.tube([(*p,4.066),(*p,4.760)],.028,'green stretcher rails',6,'slender inter-ring bar')
                if not lod:
                    # Short ties bridge the reverse curves seen between the ovals.
                    for z in (4.265,4.563):
                        left,right=[on_curve(boundary+sign*.12*pitch,.135) for sign in (-1,1)]
                        b.tube([(*left,z-.022),(*p,z+.018),(*right,z-.022)],.024,
                               'green stretcher rails',6,'short inter-ring tie')
    for sign in (-1,1):
        x=sign*(RADIUS-.135)
        for z in (4.052,4.77):
            b.tube([(x,0,z),(x,REAR,z)],.032,'green stretcher rails',6,'straight side return bar')
        for j in range(2):
            y=(j+.5)*REAR/2
            n=12 if lod else 26
            path=[(x,y+.192*cos(2*pi*k/n),4.414+.333*sin(2*pi*k/n)) for k in range(n+1)]
            b.tube(path,.047,'bronze green circles',5 if lod else 8,'side return oval')

def entrance(b,lod):
    width,height=3.34,2.34
    b.box((0,REAR+.043,height/2),(width,.13,height),'glazing in shade',label='recessed door glazing')
    for x in (-width/2,0,width/2):
        b.box((x,REAR-.052,height/2),(.105,.107,height),'timber finish',label='recessed entrance stiles')
    for z in (.065,1.06,height-.062):
        b.box((0,REAR-.05,z),(width,.108,.12),'timber finish',label='recessed entrance rails')
    for sign in (-1,1):
        left=(RADIUS-width/2)/2
        b.box((sign*(width/2+left),REAR+.165,SOFFIT/2),(2*left,.35,SOFFIT),
              'porch wall',label='shaded return beside timber opening')
    b.box((0,REAR+.165,(SOFFIT+height)/2),(width,.35,SOFFIT-height),'porch wall',label='shaded entrance lintel')
    b.plan_prism(plan(.005,24 if lod else 56),-.105,.006,'entry paving','porch paving')
    b.lathe((0,-.31),[(2.88,.021),(3.32,.021)],'pendant bronze',8,'short pendant stem')
    b.lathe((0,-.31),[(2.69,.026),(2.72,.102),(2.81,.129),(2.86,.078)],'pendant glass',
            8 if lod else 16,'hanging central globe')
    b.lathe((0,-.31),[(2.852,.088),(2.9,.048)],'pendant bronze',10,'pendant cap')

def add_building(b,lod=False):
    platform(b,lod)
    columns(b,lod)
    railing(b,lod)
    entrance(b,lod)
