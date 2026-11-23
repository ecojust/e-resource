"""Two flights of staggered steel windows on the Hankow Road garden residence."""
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

BRICK = 'burgundy face brick'
MORTAR = 'warm grey brick joint'
STONE = 'cream stair bay dressing'
CAP = 'weathered stone cap'
FRAME = 'painted dark steel'
GLASS = 'grey olive glazing'
PALETTE = {name: {'color': rgb, 'roughness': roughness} for name,rgb,roughness in [
    (BRICK,[.34,.19,.17],.93), (MORTAR,[.58,.49,.43],.98), (STONE,[.80,.77,.69],.92),
    (CAP,[.63,.62,.55],.92), (FRAME,[.22,.23,.21],.76), (GLASS,[.38,.45,.43],.42)]}

# X runs east along the source south wall. The origin is at 9.48 m from its west end.
# The model starts at 2.75 m above street grade. Dimensions come from the registered
# 2020 photograph. The pole crosses one lower opening and one upper opening.
STREET_DATUM = 2.75
AXES = (-.80,-.26,.26,.78)
UPPER_HEADS = (9.08,8.80,8.50,8.17)
LOWER_HEADS = (5.61,5.34,5.07,4.79)
HEIGHTS = (1.70,1.68,1.67,1.64)
WIDTHS = (.403,.390,.403,.409)
HALF = 1.80
MAX_Z = 9.57-STREET_DATUM

def rect(x0,z0,x1,z1):
    return box(x0,z0-STREET_DATUM,x1,z1-STREET_DATUM)

def stone_field():
    # The two edges of the pale facing step into the darker brick in alternate courses.
    spans = [rect(-1.22,2.75,1.23,9.18)]
    for z in (2.89,3.66,4.44,5.22,6.00,6.78,7.56):
        spans.extend([rect(-1.38,z,-1.21,z+.35),rect(1.22,z,1.37,z+.35)])
    spans.extend([rect(-1.38,8.36,1.37,8.79),rect(-1.26,8.79,1.25,9.35)])
    return unary_union(spans)

def stair_light(f,axis,head,height,width,detail,label):
    sill=head-height
    hole=rect(axis-width/2,sill,axis+width/2,head)
    f.prism(hole.buffer(.012,join_style=2),.118,.14,GLASS,label+' glazing')
    # A single solid steel lattice. The intermediate broad rail separates the moving
    # sash from the lower fixed lights. Avoid coincident bars at grid crossings.
    bars=[rect(axis-width/2,sill+height*.61-.027,axis+width/2,sill+height*.61+.027)]
    for fraction in (.21,.42,.80):
        z=sill+height*fraction
        bars.append(rect(axis-width/2,z-.011,axis+width/2,z+.011))
    bars.append(rect(axis-.010,sill,axis+.010,head))
    pane=hole.buffer(-.033,join_style=2).difference(unary_union(bars))
    f.prism(hole.difference(pane),.143,.184,FRAME,label+' steel grid')
    f.prism(rect(axis-width/2-.034,sill-.047,axis+width/2+.033,sill),.18,.339,CAP,label+' sill')
    if detail:
        # The upper three pane edges catch light on the rebate of the steel frame.
        inset=hole.buffer(-.031,join_style=2)
        lip=inset.difference(inset.buffer(-.009,join_style=2))
        f.prism(lip,.181,.197,FRAME,label+' steel rebate')
    return hole

def joints(f,region):
    marks=[]
    for i in range(90):
        z=2.75+i*.079
        if z>9.52: break
        marks.append(rect(-HALF,z,HALF,z+.007))
        for k in range(-9,10):
            x=k*.255+(.128 if i%2 else 0)
            marks.append(rect(x,z+.006,x+.007,z+.079))
    exposed=region.intersection(unary_union(marks))
    f.prism(exposed,.221,.226,MORTAR,'staggered brick joints')

def add_building(builder,lod):
    f=Facade(builder,(-HALF,0),(HALF,0),'Stair bay')
    # The full hill of the roof continues beyond the photographed bay. Only the
    # dark brick shoulders immediately beside the high central stair casing are present.
    side_wall=rect(-HALF,2.75,HALF,7.73)
    high_wall=Polygon([(-1.36,7.64-STREET_DATUM),(-1.39,8.89-STREET_DATUM),
                       (-1.23,9.26-STREET_DATUM),(-1.18,9.55-STREET_DATUM),
                       (1.16,9.51-STREET_DATUM),(1.24,9.29-STREET_DATUM),
                       (1.38,8.88-STREET_DATUM),(1.39,7.64-STREET_DATUM)])
    field=stone_field()
    outline=unary_union([side_wall,high_wall,field])
    brick=outline.difference(field)
    f.prism(brick,.08,.22,BRICK,'brick shoulders')
    if not lod: joints(f,brick)
    holes=[]
    for row,heads in [('upper',UPPER_HEADS),('lower',LOWER_HEADS)]:
        for i,(x,head,height,width) in enumerate(zip(AXES,heads,HEIGHTS,WIDTHS)):
            holes.append(stair_light(f,x,head,height,width,not lod,row+' '+str(i+1)))
    f.prism(field.difference(unary_union(holes)),.077,.299,STONE,'eight open stepped reveals')
    # The cap is straight while the steel-window heads walk down towards the east.
    f.prism(rect(-1.17,9.29,1.17,9.46),.22,.332,STONE,'raised head band')
    f.prism(rect(-1.16,9.46,1.16,9.54),.21,.365,CAP,'head cap')
    for x in (-1.10,1.08):
        f.prism(rect(x-.089,8.91,x+.089,9.41),.276,.349,STONE,'upper side block')
    for x in (-.78,-.24,.27,.80):
        f.prism(rect(x-.17,9.17,x+.17,9.30),.294,.344,STONE,'stone below head band')
