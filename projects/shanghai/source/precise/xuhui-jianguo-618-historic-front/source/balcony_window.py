"""Upper balcony and lower glazing in the institutional photograph taken 10 July 2013."""
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade

WALL = 'ivory rendered wall'
REVEAL = 'shadowed window reveals'
FRAME = 'painted ivory sash'
GLASS = 'pale blue window glass'
GASKET = 'dark window seal'
JOINT = 'shadow in facade joint'
EDGE = 'light concrete face'
SOFFIT = 'warm concrete soffit'
RAIL = 'light balcony coping'
FLOOR = 'grey balcony deck'
PALETTE = {
    WALL: {'color': [.855, .847, .815], 'roughness': .91},
    REVEAL: {'color': [.644, .613, .546], 'roughness': .86},
    FRAME: {'color': [.879, .883, .855], 'roughness': .56},
    GLASS: {'color': [.442, .570, .627], 'roughness': .35, 'metallic': .23},
    GASKET: {'color': [.212, .251, .248], 'roughness': .69},
    JOINT: {'color': [.561, .569, .547], 'roughness': .93},
    EDGE: {'color': [.826, .827, .786], 'roughness': .85},
    SOFFIT: {'color': [.736, .715, .651], 'roughness': .91},
    RAIL: {'color': [.814, .828, .820], 'roughness': .69},
    FLOOR: {'color': [.535, .549, .520], 'roughness': .91},
}
# These two frames share the photographed right jamb. The lower bay has two broad
# toplights above four casements. Only the right-hand pair is fully exposed.
LOWER = (-2.00, .18, .96, 2.10, 1.43, 4)
UPPER = (-.76, 3.54, .96, 5.63, 5.00, 2)
SPAN = 2.45
TOP = 6.13


def glazing(f, spec, low):
    x0, z0, x1, z1, rail, leaves = spec
    opening = box(x0, z0, x1, z1)
    inner = box(x0+.047, z0+.055, x1-.047, z1-.047)
    f.prism(opening.difference(inner), -.146, -.055, REVEAL, 'recessed jamb and lintel')
    f.prism(inner, -.140, -.126, GLASS, 'recessed glass planes')
    w = (x1-x0)/leaves
    for count, bottom, top in [(leaves, z0+.041, rail), (leaves//2, rail, z1-.040)]:
        width = (x1-x0)/count
        for i in range(count):
            left = x0+i*width+.025
            right = x0+(i+1)*width-.025
            outer = box(left, bottom, right, top)
            pane = box(left+.067, bottom+.059, right-.067, top-.062)
            f.prism(outer.difference(pane), -.131, -.053, FRAME, 'separate casement and toplight sashes')
            if not low:
                f.prism(pane.difference(pane.buffer(-.009, join_style=2)), -.123, -.101,
                        GASKET, 'inset glazing rebates')
    f.prism(box(x0+.035, rail-.034, x1-.035, rail+.034), -.099, -.036, FRAME, 'continuous transom rail')
    f.prism(box(x0-.018, z0-.040, x1+.018, z0), -.052, .027, EDGE, 'flat sill lip')
    # The modular sash joins remain narrow, closed at the back by the glass.
    for i in range(1, leaves):
        x=x0+i*w
        f.prism(box(x-.024, z0+.042, x+.024, rail-.036), -.129, -.079, FRAME, 'vertical frame between casements')
    if leaves == 4:
        x=(x0+x1)/2
        f.prism(box(x-.024, rail+.03, x+.024, z1-.042), -.129, -.079, FRAME, 'upper double transom mullion')


def make_front(b, low=False):
    f=Facade(b, (-SPAN,0), (SPAN,0), 'photographed window bay')
    boundary=box(-SPAN,0,SPAN,TOP)
    lights=unary_union([box(*spec[:4]) for spec in (LOWER,UPPER)])
    # Fine grooves are recessed into the face, with a continuous back layer.
    lines=[box(-SPAN,z-.007,SPAN,z+.007) for z in (.18,2.10,3.04,4.06,5.08)]
    lines.extend(box(x-.006,0,x+.006,TOP) for x in (-2.0,.96,2.05))
    cuts=unary_union(lines)
    f.prism(boundary.difference(lights),-.245,-.018,JOINT,'back of actual control joints')
    f.prism(boundary.difference(lights.union(cuts)),-.024,0,WALL,'rendered wall panels')
    for spec in (LOWER,UPPER):
        glazing(f,spec,low)
    # The plate projects beyond the two windows. Its hollow upper edge and the
    # open slot below the top rail are visible at the right end of the photograph.
    left,right=-1.68,1.78
    width=right-left
    cx=(left+right)/2
    def cub(label, x, y, z, dx, dy, dz, material):
        b.box((x,y,z),(dx,dy,dz),material,label=label)
    cub('balcony plate and exposed fascia',cx,-.532,3.38,width,1.12,.23,EDGE)
    cub('light underside of the cantilever',cx,-.529,3.259,width-.008,1.11,.012,SOFFIT)
    cub('upper face of the balcony deck',cx,-.524,3.508,width-.056,1.048,.026,FLOOR)
    cub('solid front parapet',cx,-1.034,3.875,width,.116,.748,EDGE)
    for x in (left+.056,right-.056):
        cub('balcony side returns',x,-.505,3.875,.112,.985,.748,EDGE)
    for x in (left+.087,cx,right-.087):
        cub('short supports below top rail',x,-1.035,4.289,.070,.058,.088,RAIL)
    cub('thin elevated front rail',cx,-1.035,4.363,width+.018,.095,.070,RAIL)
    for x in (left+.061,right-.061):
        cub('thin return rail',x,-.505,4.363,.099,1.00,.070,RAIL)
    if not low:
        cub('fine drip on front lip',cx,-1.053,3.248,width-.066,.024,.014,EDGE)
        for x in (left+.060,right-.060):
            cub('side flange beneath coping',x,-.40,4.293,.052,.065,.082,RAIL)
    f.prism(box(-SPAN,5.969,SPAN,6.071),-.047,.102,WALL,'horizontal fascia above window')
    f.prism(box(-SPAN,6.073,SPAN,TOP),-.050,.144,EDGE,'projecting cornice lip')
