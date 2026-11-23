"""One elevated window, its shallow canopy and the visible parapet on the west face."""
from shapely.geometry import box
from photo_architecture import Facade

PALETTE = {
    'rose brick': {'color': [.58,.34,.29], 'roughness': .92},
    'orange brick': {'color': [.57,.30,.25], 'roughness': .92},
    'brown brick': {'color': [.49,.27,.23], 'roughness': .94},
    'recessed joint': {'color': [.36,.27,.24], 'roughness': .98},
    'molded brick': {'color': [.54,.30,.25], 'roughness': .89},
    'coping stone': {'color': [.47,.43,.37], 'roughness': .87},
    'bronze sash': {'color': [.23,.20,.16], 'roughness': .74},
    'reflecting glass': {'color': [.27,.32,.33], 'roughness': .31},
    'canopy face': {'color': [.47,.32,.27], 'roughness': .87},
    'canopy soffit': {'color': [.34,.26,.24], 'roughness': .93},
}

BASE_Z = 7.32
WIDTH = 2.43
TOP = 11.54 - BASE_Z
# The lower extent of the glazing is hidden behind the parapet in both dated surveys.
OPENING = (-.407, 7.94-BASE_Z, .457, 9.55-BASE_Z)
HOOD_HEAD = 9.965-BASE_Z
HOOD_EDGE = 9.745-BASE_Z
HOOD_WIDTH = 1.53

def brickwork(f, mask, depth, lod, label):
    """Lay staggered stretchers; clipped courses stop exactly at jambs and cap."""
    x0,z0,x1,z1=mask.bounds
    f.prism(mask,depth-.065,depth-.018,'recessed joint',label+' mortar')
    if lod:
        f.prism(mask,depth-.018,depth,'rose brick',label+' brick face')
        # Three genuinely modeled horizontal bed joints remain legible at this scale.
        for idx,z in enumerate((z0+.085,z0+.243,z0+.400)):
            course=box(x0,z-.009,x1,z+.009).intersection(mask)
            if course.area>0:
                f.prism(course,depth,depth+.003,'recessed joint',label+' beds '+str(idx))
        return
    pitch=.074
    row=0
    while z0+row*pitch<z1:
        lower=z0+row*pitch
        height=min(z1-.002,lower+pitch-.005)
        if height<=lower+.003:
            break
        left=x0-.257*(row%2)*.5
        col=0
        while left<x1:
            shape=box(left+.004,lower+.003,min(x1+.275,left+.253),height).intersection(mask)
            if shape.area>.00008:
                mats=('rose brick','rose brick','orange brick','brown brick','rose brick')
                f.prism(shape,depth-.019,depth+((row+col)%3)*.0015,
                        mats[(row*3+col)%len(mats)],label+' course '+str(row))
            left+=.257
            col+=1
        row+=1

def canopy(f):
    """The two photographs show a straight fascia and a sloping upper surface."""
    section=[(0,HOOD_HEAD),(.49,HOOD_EDGE+.082),(.49,HOOD_EDGE),(.0,HOOD_HEAD-.087)]
    vertices=[f.point(x,z,d) for x in (-HOOD_WIDTH/2,HOOD_WIDTH/2) for d,z in section]
    f.builder.add(vertices,[(0,1,5,4),(1,2,6,5),(0,3,2,1),(4,5,6,7),(3,0,4,7)],
                  'canopy face','upper window/projecting hood')
    f.builder.add(vertices,[(2,3,7,6)],'canopy soffit','upper window/hood underside')

def add_building(builder,lod=False):
    f=Facade(builder,(-WIDTH/2,0),(WIDTH/2,0),'upper west bay')
    x0,z0,x1,z1=OPENING
    clear=box(*OPENING)
    wall=box(-WIDTH/2,0,WIDTH/2,TOP).difference(clear)
    f.prism(wall,-.32,-.07,'brown brick','jamb depth')
    brickwork(f,wall,0,lod,'field')
    opening=clear.buffer(-.055,join_style=2)
    f.prism(clear.difference(opening),-.195,-.115,'bronze sash','recessed frame')
    f.prism(opening,-.218,-.202,'reflecting glass','glazing')
    center=(x0+x1)/2
    f.box(center,(z0+z1)/2,.030,z1-z0-.10,.037,-.139,'bronze sash','meeting rail')
    for i,z in enumerate((8.55-BASE_Z,9.16-BASE_Z)):
        f.box(center,z,x1-x0-.075,.035,.037,-.139,'bronze sash','cross rail '+str(i))
    if not lod:
        for i,x in enumerate((center-.192,center+.192)):
            f.box(x,8.25-BASE_Z,.020,.52,.023,-.156,'bronze sash','lower glazing bar '+str(i))
    canopy(f)
    # Raised brick stringing framing the upper window and building cornice.
    for i,(e,h,d) in enumerate([(8.92,.035,.058),(9.18,.045,.061),
                                 (10.54,.063,.077),(11.12,.090,.089),
                                 (11.225,.060,.111),(11.305,.075,.144),
                                 (11.395,.090,.175),(11.495,.085,.215)]):
        z=e-BASE_Z
        band=box(-WIDTH/2,z-h/2,WIDTH/2,z+h/2).difference(clear)
        f.prism(band,-.006,d,'molded brick','brick band '+str(i))
    # Only the top of this parapet is documented at the chosen bay. Its forward
    # offset is separately triangulated from its left coping corner.
    parapet=box(-WIDTH/2,0,WIDTH/2,7.82-BASE_Z)
    f.prism(parapet,.94,1.072,'brown brick','parapet core')
    brickwork(f,parapet,1.09,lod,'parapet')
    for i,(z,h,d) in enumerate(((7.818,.052,.139),(7.862,.040,.172))):
        f.box(0,z-BASE_Z,WIDTH+.018,h,d,1.038,'coping stone','parapet coping '+str(i))
