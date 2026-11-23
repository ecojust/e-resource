"""Editable stepped plaster plaques and paired scroll reliefs from the 2019 exterior photograph."""
import json
import math
from pathlib import Path

from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from materials import PALE, SHADE
from photo_plane import hit

OBSERVATIONS = Path(__file__).resolve().parent.parent / 'measurements/scroll-panel-observations.json'

# Hand-read left scroll and leaf centrelines in each plaque's own width and height.
# The third ordinate controls the changing width of the leaf in fractions of plaque height.
WINDOW_SCROLL = [
    (.49,.35,.024),(.45,.33,.046),(.40,.34,.070),(.36,.40,.075),
    (.343,.48,.072),(.352,.55,.074),(.382,.578,.078),(.411,.544,.075),
    (.422,.483,.064),(.410,.456,.030),(.394,.46,.010)
]
WINDOW_LEAVES = [
    [(.472,.32,.012),(.47,.46,.060),(.465,.57,.095),(.445,.647,.095),(.409,.687,.074),(.356,.687,.050),(.302,.65,.016)],
    [(.384,.633,.020),(.328,.601,.077),(.293,.54,.086),(.266,.484,.075),(.229,.471,.062),(.207,.51,.081),(.169,.49,.068),(.142,.426,.09),(.123,.372,.030)],
    [(.47,.66,.018),(.453,.722,.076),(.430,.755,.084),(.408,.752,.012)],
    [(.356,.686,.010),(.35,.737,.044),(.326,.755,.055),(.317,.746,.012)]
]
LINTEL_SCROLL = [
    (.486,.617,.026),(.463,.665,.071),(.429,.675,.086),(.401,.627,.084),
    (.386,.552,.081),(.389,.477,.085),(.414,.439,.080),(.439,.456,.067),
    (.449,.504,.055),(.433,.535,.043),(.424,.522,.012)
]
LINTEL_LEAVES = [
    [(.495,.654,.014),(.462,.706,.092),(.431,.748,.109),(.400,.755,.085),(.373,.722,.032)],
    [(.396,.727,.025),(.358,.768,.097),(.332,.766,.086),(.31,.713,.088),(.289,.682,.047),(.268,.721,.096),(.247,.77,.08),(.217,.774,.06),(.193,.727,.083),(.178,.69,.068),(.163,.708,.086),(.146,.742,.068),(.122,.728,.042),(.109,.696,.012)],
    [(.467,.736,.027),(.456,.788,.065),(.439,.811,.032),(.427,.804,.012)]
]

def smooth(knots, steps):
    extended = [knots[0]] + list(knots) + [knots[-1]]
    points = []
    for i in range(len(knots)-1):
        a,b,c,d = extended[i:i+4]
        for j in range(steps):
            t = j/steps
            points.append(tuple(.5*(2*v+(-u+w)*t+(2*u-5*v+4*w-q)*t*t+
                                 (-u+3*v-3*w+q)*t**3) for u,v,w,q in zip(a,b,c,d)))
    return points+[knots[-1]]

def ribbon(knots, width, height, steps, factor=1.0):
    pts = [(x*width,(1-y)*height,max(r,.004)*height*factor) for x,y,r in smooth(knots,steps)]
    left,right = [],[]
    for i,(x,z,diameter) in enumerate(pts):
        ax,az,_ = pts[max(0,i-1)]
        bx,bz,_ = pts[min(len(pts)-1,i+1)]
        scale = diameter/(2*math.hypot(bx-ax,bz-az))
        dx,dz = (az-bz)*scale,(bx-ax)*scale
        left.append((x+dx,z+dz))
        right.append((x-dx,z-dz))
    return Polygon(left+right[::-1]).buffer(0)

def measured_layout():
    rows = []
    for observation in json.loads(OBSERVATIONS.read_bytes())['panels']:
        tl,tr,bottom = [hit(*p) for p in observation['bounds']]
        rows.append(dict(id=observation['id'],kind=observation['kind'],x=(tl[0]+tr[0])/2,
                         z=bottom[1],width=tr[0]-tl[0],height=(tl[1]+tr[1])/2-bottom[1]))
    return rows

def add_scroll_panel(front, row, lod=False):
    """Place one historic relief. x is its centre, z its bottom and projection grows towards the viewer."""
    kind = row['kind']
    w,h = row['width'],row['height']
    p = row.get('projection',.0)
    if kind not in ('window','shutter','lintel') or min(w,h)<=0:
        raise ValueError('Expected window, shutter or lintel with positive width and height')
    lintel = kind == 'lintel'
    quarter, shoulder = ((.232,.65) if lintel else (.209,.34) if kind=='window' else (.219,.33))
    center = box(quarter*w,0,(1-quarter)*w,h)
    slab = center.union(box(0,0,w,shoulder*h) if lintel else box(0,shoulder*h,w,h))
    shifts = (row['x']-w/2,row['z'])
    def cast(shape, back, face, material, label):
        front.solid(affinity.translate(shape,*shifts),p+back,p+face,material,f"{row['id']} {label}")
    thickness = row.get('backing',min(.055,.12*h))
    relief = row.get('relief',min(.037,.082*h))
    cast(slab,-.003,thickness*.72,SHADE,'shadowed substrate')
    # A recessed straight channel under each lip is cut all the way through this face coat.
    # The lower, solid substrate forms each channel floor.
    if lintel:
        strips = [(.255,.745,.88),(.273,.727,.805),(.025,.975,.075),
                  (.024,.208,.566),(.792,.976,.566),(.042,.206,.51),(.794,.958,.51)]
    else:
        strips = [(.044,.956,.887),(.060,.940,.816),(.24,.76,.115),
                  (.034,.185,shoulder+.073),(.815,.966,shoulder+.073)]
    ribs = [box(a*w,(z-.009)*h,b*w,(z+.009)*h) for a,b,z in strips]
    cuts = unary_union(ribs)
    cast(slab.difference(cuts),thickness*.72,thickness,PALE,'stepped face with sunk fillets')
    scrolls = ([LINTEL_SCROLL]+LINTEL_LEAVES) if lintel else ([WINDOW_SCROLL]+WINDOW_LEAVES)
    steps = 2 if lod else 4
    for i,knots in enumerate(scrolls):
        left = ribbon(knots,w,h,steps)
        crest = ribbon(knots,w,h,steps,.46)
        for side,geometry,highlight in [('left',left,crest),('right',affinity.scale(left,xfact=-1,origin=(w/2,0)),
                                                            affinity.scale(crest,xfact=-1,origin=(w/2,0)))]:
            cast(geometry,thickness,thickness+relief*.64,PALE,f'{side} scroll {i+1}')
            if not lod or i==0:
                cast(highlight,thickness+relief*.64,thickness+relief,PALE,f'{side} raised crest {i+1}')

def add_scroll_panels(front, lod=False, layout=None):
    for row in measured_layout() if layout is None else layout:
        add_scroll_panel(front,row,lod)
