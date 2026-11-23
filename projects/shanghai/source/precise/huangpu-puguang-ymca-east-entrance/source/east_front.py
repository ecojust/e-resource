"""The windows, split pediment, and two shopfronts beside the Puguang entrance."""
from math import cos,pi,sin
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union
from photo_architecture import Facade
from brick_finish import TEXTURE,texture_uv
from stone_entrance import PORTAL_MATERIALS,add_entrance

BRICK='exposed warm Shanghai brick'
BRICK_RING=('pink radial brick','orange radial brick','umber radial brick')
MORTAR='recessed tan mortar'
RUSTICATION='deep bed in channelled brickwork'
BAND='sand grey pediment stone'
CAP='edge of pediment stone'
PAVING='grey frontage plinth'
WOOD='reddish brown shop sash'
GLASS='shadow glass in shop fanlights'
WINDOW='sky grey upper glass'
SHUTTER='pale blue grey shutter'
SEAM='shutter profile shadows'
CORNICE='brown brick string course'
PALETTE={k:{'color':v,'roughness':r} for k,v,r in [
    (BRICK,[1,1,1],.89),(BRICK_RING[0],[.58,.32,.22],.84),(BRICK_RING[1],[.63,.36,.25],.85),
    (BRICK_RING[2],[.50,.27,.20],.85),(MORTAR,[.52,.43,.36],.95),(BAND,[.55,.53,.45],.84),
    (RUSTICATION,[.34,.20,.15],.94),(CAP,[.67,.63,.55],.87),(PAVING,[.44,.43,.41],.92),(WOOD,[.27,.135,.115],.69),
    (GLASS,[.12,.20,.21],.35),(WINDOW,[.43,.57,.63],.34),(SHUTTER,[.66,.70,.72],.75),
    (SEAM,[.42,.46,.48],.77),(CORNICE,[.43,.25,.20],.87)]}
PALETTE[BRICK]['texture']=str(TEXTURE)
PALETTE.update(PORTAL_MATERIALS)
GROUND_WIDTH=19.43
UPPER_WIDTH=15.25
STRING=7.095
TOP=15.04

def shop_shape(x,r,spring,rise,steps):
    arch=[(x+r*cos(i*pi/steps),spring+rise*sin(i*pi/steps))for i in range(steps+1)]
    return Polygon([(x-r,-.02),(x+r,-.02),*arch])

def framed(face,shape,x,z,w,h,lod,upper=False):
    a,b,c,d=shape.bounds
    inner=shape.buffer(-.064,join_style='mitre')
    bars=[box(x-.029,b,x+.029,d)]
    if upper:
        bars.append(box(a,b+h*.65-.03,c,b+h*.65+.03))
    else:
        bars.extend(box(x+f*w-.025,b,x+f*w+.025,d)for f in (-.25,.25))
    frame=shape.difference(inner.difference(unary_union(bars)))
    face.prism(shape,-.32,-.27,WINDOW if upper else GLASS,'upper panes' if upper else 'shop panes')
    face.prism(frame,-.20,-.103,WOOD,'upper timber sash' if upper else 'shop timber sash')

def shopfront(face,side,lod):
    x,r,sp,rise=((-6.895,2.185,4.535,1.08)if side<0 else(6.99,2.12,4.57,.985))
    lo,hi=((-9.715,-3.97)if side<0 else(3.92,9.715))
    steps=20 if lod else 44
    opening=shop_shape(x,r,sp,rise,steps)
    ring=shop_shape(x,r+.33,sp,rise+.36,steps).difference(opening).intersection(box(lo,sp-.004,hi,STRING))
    wall=box(lo,0,hi,STRING).difference(opening)
    face.prism(wall,-1.49,-.022,BRICK,'shop masonry and jamb')
    face.prism(ring,-.024,.058,MORTAR,'bedding around shop arch')
    # Each tapered fired brick follows the ellipse between spring and crown.
    count=17 if lod else 31
    for i in range(count):
        angles=[(i+f)*pi/count for f in (.045,.49,.955)]
        points=[(x+(r+.32)*cos(t),sp+(rise+.355)*sin(t))for t in angles]
        points.extend((x+(r+.003)*cos(t),sp+(rise+.005)*sin(t))for t in reversed(angles))
        face.prism(Polygon(points),.045,.093,BRICK_RING[(i+int(side>0))%3],'radial voussoirs')
    for direction in (-1,1):
        c=x+direction*(r+.19)
        face.box(c,2.215,.35,4.43,.35,-.075,PAVING,'spring pier')
        face.box(c,4.475,.52,.15,.44,-.047,BAND,'stone impost')
    key=Polygon([(x-.16,sp+rise+.035),(x+.16,sp+rise+.035),(x+.29,6.71),(x-.29,6.71)])
    face.prism(key,.083,.177,CAP,'shop arch keystone')
    transom=opening.intersection(box(lo,sp-.19,hi,7))
    inner=transom.buffer(-.055,join_style='mitre')
    bars=[box(x+f*r-.035,sp-.21,x+f*r+.035,sp+rise+.03)for f in (-.72,-.37,0,.37,.72)]
    bars.append(box(x-r,sp+.27,x+r,sp+.33))
    face.prism(transom,-.46,-.39,GLASS,'curved shop fanlight glass')
    face.prism(transom.difference(inner.difference(unary_union(bars))),-.31,-.218,WOOD,'curved fanlight sash')
    face.box(x,sp-.225,2*r+.04,.13,.26,-.17,WOOD,'fanlight rail')
    if side<0:
        glass=box(x-r+.15,1.60,x+r-.15,2.84)
        fill=box(x-r,0,x+r,sp-.26).difference(glass)
        face.prism(fill,-.67,-.274,BRICK,'south shop later brick infill')
        framed(face,glass,x,2.22,glass.bounds[2]-glass.bounds[0],1.24,lod)
        face.box(x,.22,2*r,.44,.24,-.21,PAVING,'south shop plinth')
    else:
        fascia=box(x-r,sp-.63,x+r,sp-.26)
        face.prism(fascia,-.53,-.255,BRICK,'north shutter fascia')
        face.prism(box(x-r,.085,x+r,sp-.64),-.46,-.33,SHUTTER,'north rolling shutter')
        for j in range(1,29 if lod else 55):
            z=.08+(sp-.74)*j/(29 if lod else 55)
            face.box(x,z,2*r-.04,.024 if lod else .014,.022,-.32,SEAM,'shutter slat joints')
        for c in [x-r+.055,x+r-.055]:
            face.box(c,(sp-.61)/2,.093,sp-.65,.25,-.23,SEAM,'shutter side guides')
        face.box(x,.045,2*r,.09,.82,-.20,PAVING,'north shop threshold')

def upper(face,lod):
    apertures=[]
    for x in (-5.69,.08,5.75):
        for row in (0,1):
            central=abs(x)<.5
            if row==0:
                lo,hi=(6.37,10.28) if central else (8.10,10.05)
            else:
                lo,hi=(12.56,14.03) if central else (12.46,13.98)
            width=1.71 if central else 1.63
            hole=box(x-width/2,lo,x+width/2,hi)
            apertures.append(hole)
            framed(face,hole,x,(lo+hi)/2,width,hi-lo,lod,upper=True)
            face.box(x,lo-.066,width+.23,.13,.43,-.038,BAND,'window sill')
            face.box(x,hi+.095,width+.31,.19,.31,-.089,BRICK_RING[2],'brick lintel')
    # The central sash descends below the side capitals to the top of the English lintel.
    wall=box(-UPPER_WIDTH/2,STRING,UPPER_WIDTH/2,TOP).union(box(-1.74,6.37,1.74,STRING+.005))
    face.prism(wall.difference(unary_union(apertures)),
               -1.49,-.022,BRICK,'original brick street wall with six window reveals')
    for side in (-1,1):
        c=side*2.91
        face.box(c,9.395,1.60,4.60,.30,.074,RUSTICATION,'pilaster brick core')
        # Deep joints on the rectangular pilaster flank its circular attached shaft.
        for i in range(9):
            face.box(c,7.42+i*.438,1.55,.384,.35,.137,BRICK,'channelled brick courses')
        inner=side*2.05
        coords=[(inner+.256*cos(i*2*pi/(16 if lod else 36)),-.255+.256*sin(i*2*pi/(16 if lod else 36)))for i in range(16 if lod else 36)]
        face.builder.plan_prism(Polygon(coords),7.51,11.20,BRICK_RING[1],'attached brick column')
        for z,width,height,depth in [(7.45,.70,.13,.54),(7.55,.58,.11,.49),(11.20,.61,.19,.56),(11.36,.78,.14,.70),(11.48,.84,.12,.79)]:
            face.box(inner,z,width,height,depth,.22,CAP,'square capital and plinth')
        for z,width,h,depth in [(11.54,2.27,.17,.59),(11.69,2.44,.17,.70),(11.82,2.57,.13,.78)]:
            face.box(side*2.69,z,width,h,depth,.199,BAND if z<11.8 else CAP,'broken pediment spring courses')
        # Both raking cornices stop before the central upper sash.
        a,b=(side*3.12,11.83),(side*1.42,13.18)
        outline=Polygon([a,b,(b[0],b[1]-.51),(a[0],a[1]-.21)])
        face.prism(outline,.10,.39,BAND,'split pediment cheek')
        for lift,width,projection,material in [(0,.14,.44,BAND),(.135,.112,.52,CAP)]:
            strip=LineString([(a[0]+side*.18,a[1]+lift-.12),(b[0],b[1]+lift)]).buffer(width/2,cap_style='flat')
            face.prism(strip,.24,projection,material,'raking pediment crown')
    for z,w,h,d in [(6.82,GROUND_WIDTH,.095,.116),(7.015,GROUND_WIDTH,.16,.185),(7.103,UPPER_WIDTH,.078,.165)]:
        for side in (-1,1):
            start,end=1.74,w/2
            face.box(side*(start+end)/2,z,end-start,h,.25+d,d/2-.09,
                     BAND if z>7 else CORNICE,'first storey stringcourse')

def add_building(builder,lod):
    face=Facade(builder,[-GROUND_WIDTH/2,0],[GROUND_WIDTH/2,0],'Sichuan Road')
    for side in (-1,1):shopfront(face,side,lod)
    add_entrance(face,lod)
    upper(face,lod)
    for part in builder.parts:
        if part['material']==BRICK:
            part['texcoords']=[(u,1-v)for u,v in (texture_uv(*pt)for pt in part['vertices'])]
