"""Hand-built steel transoms and sashes from the 2023 district detail photographs."""
from shapely.geometry import box
from shapely.ops import unary_union
from street_finish import GLASS,GROUND_GLASS,STEEL,TRIM,TERRAZZO,BASE,IRON,GOLD,TIMBER

def frame(face,width,bottom,top,lod,style):
    high=top-bottom
    slot=box(-width/2,bottom,width/2,top)
    ground=style in ('door','shop')
    depth=-.39 if ground else -.25
    face.prism(slot.buffer(.036,join_style='mitre'),depth-.045,depth-.02,GROUND_GLASS if ground else GLASS,'glazing')
    border=slot.buffer(.006,join_style='mitre')
    inner=slot.buffer(-.055,join_style='mitre')
    if style=='door':
        # Three glazed shopfront panels form the photographed angle entrance.
        bars=[box(x-.042,bottom,x+.042,top) for x in (-width/6,width/6)]
        for z in (bottom+high*.29,bottom+high*.78):
            bars.append(box(-width/2,z-.032,width/2,z+.032))
        face.box(width*.11,1.12,.050,.34,.08,depth+.115,GOLD,'brass gate pull')
        for i,(front,level) in enumerate([(.13,.09),(-.02,.18),(-.15,bottom)]):
            face.box(0,level/2,width+.08,level,.18,front,TERRAZZO,'entry threshold')
    elif style=='shop':
        bars=[box(x-.022,bottom,x+.022,top)for x in (-width/6,width/6)]
        bars.append(box(-width/2,bottom+high*.75,width/2,bottom+high*.75+.065))
        face.box(0,.07,width,.14,.24,-.08,BASE,'shop threshold')
    elif style=='attic':
        bars=[box(-width/2,top-high*.22,width/2,top-high*.22+.040)]
        if width>1.3:
            for x in (-width/6,width/6):bars.append(box(x-.022,bottom,x+.022,top))
        else:bars.append(box(-.025,bottom,.025,top))
    else:
        # Three parallel horizontal bars and paired narrow verticals form
        # the upper decorative band. They remain independent of street wires.
        bars=[]
        for frac in (.28,.32,.365):
            z=top-high*frac
            bars.append(box(-width/2,z-.018,width/2,z+.018))
        for frac in (-.36,-.13,.13,.36):
            x=width*frac
            bars.append(box(x-.019,bottom,x+.019,top))
            if not lod:
                bars.append(box(x+.059,bottom,x+.081,top))
        if not lod:
            for x in (-width*.27,width*.27):
                bars.append(box(x-.012,top-high*.28,x+.012,top))
    face.prism(border.difference(inner.difference(unary_union(bars))),depth+.035,depth+.103,STEEL,'welded steel frame')
    if not ground:face.box(0,bottom-.068,width+.15,.136,.43,.023,TRIM,'stone sill')
    return slot
