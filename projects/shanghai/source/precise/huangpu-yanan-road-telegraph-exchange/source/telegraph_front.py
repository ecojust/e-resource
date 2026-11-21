"""Photographed south street elevation of the Shanghai Telegraph Building, in metres."""
from math import cos, pi, sin
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering, lettering_shapes

ASHLAR = 'buff sandstone'
CARVED = 'light dressed limestone'
SHADE = 'recessed stone'
FIELD = 'ochre stone face'
GLASS = 'grey green window glass'
SASH = 'charcoal metal casement'
DOOR = 'bronze entry door'
CANOPY = 'green-grey canopy glass'
BOARD = 'black museum sign'
GOLD = 'gilded sign characters'
ROOF = 'grey roof cap'
PALETTE = {name: {'color': rgb, 'roughness': rough} for name, rgb, rough in [
    (ASHLAR, [.74,.64,.52], .89), (CARVED, [.86,.78,.65], .83),
    (SHADE, [.56,.48,.38], .91), (FIELD,[.70,.61,.50],.88), (GLASS, [.20,.30,.32], .23),
    (SASH, [.11,.12,.11], .58), (DOOR, [.16,.16,.13], .53),
    (CANOPY, [.43,.56,.54], .29), (BOARD, [.075,.076,.065], .46),
    (GOLD, [.94,.73,.29], .42), (ROOF, [.39,.40,.37], .84)]}
HALF, FACE, BACK = 14.82, .91, 3.05
CENTERS = [-6.25,-3.75,-1.25,1.25,3.75,6.25]
WINGS = [-12.65,-10.12,10.12,12.65]
PORTALS = [-11.70,0,11.70]
FONT = Path(__file__).with_name('museum-sign.otf')


def band(f,x,z,w,h,d,thick,material,label):
    f.box(x,z,w,h,thick,d,material,label)


def stone_courses(f,outline,holes,lod):
    joints = unary_union([h.buffer(.025,join_style=2) for h in holes])
    regions = [(-HALF,HALF,.16,8.18),(-HALF,-8.07,8.18,22.3),(8.07,HALF,8.18,22.3)]
    for left,right,low,high in regions:
        count=round((high-low)/.61)
        dz=(high-low)/count
        for n in range(count):
            z=low+n*dz
            if lod:
                course=box(left,z+.035,right,z+dz-.026).intersection(outline).difference(joints)
                if not course.is_empty:f.prism(course,.008,.042,ASHLAR,'horizontal face course')
            else:
                step=2.38
                for i in range(-1,int((right-left)/step)+1):
                    first=left+i*step+(n%2)*step/2
                    a=max(left,first+.022);b=min(right,first+step-.022)
                    if b<a+.045:continue
                    stone=box(a,z+.025,b,z+dz-.022).intersection(outline).difference(joints)
                    if not stone.is_empty and stone.area>.007:f.prism(stone,.006,.06,ASHLAR,'rusticated face block')


def window(f,x,z,w,h,lod,label,fan=False):
    hole=opening(x,z,w,h)
    f.window(hole,columns=1 if lod else 2,rows=2,frame=SASH,glass=GLASS,trim=False,label=label)
    f.builder.parts.pop()
    band(f,x,z-.055,w+.16,.11,.052,.25,CARVED,label+' sill')
    if fan and not lod:
        for sign in [-1,1]:
            path=LineString([(x,z+h-.47),(x+sign*(w/2-.1),z+h-.13)])
            f.prism(path.buffer(.016,cap_style=2),-.15,-.085,SASH,'angled transom')
    return hole


def roundel(f,x,z,lod):
    count=12 if lod else 24;rad=.23
    disc=Polygon([(x+rad*cos(2*pi*i/count),z+rad*sin(2*pi*i/count))for i in range(count)])
    f.prism(disc,.165,.205,SHADE,'roundel shadow')
    f.prism(disc.difference(disc.buffer(-.04)),.201,.262,CARVED,'window apron roundel rim')
    core=Point(x,z).buffer(.046,quad_segs=3 if lod else 6)
    f.prism(core,.202,.282,CARVED,'roundel centre')
    if not lod:
        for i in range(6):
            a=i*pi/3
            leaf=Polygon([(x+.045*cos(a),z+.045*sin(a)),(x+.105*cos(a-.31),z+.105*sin(a-.31)),
                          (x+.169*cos(a),z+.169*sin(a)),(x+.105*cos(a+.31),z+.105*sin(a+.31))])
            f.prism(leaf,.202,.254,CARVED,'six radiating rosette petals')


def portal(f,x,lod):
    # The photographed curved stone head sits above the flat glazed entrance canopy.
    hole=opening(x,.05,2.55,3.66,.52,segments=12 if lod else 24)
    surround=hole.buffer(.19,join_style=2).difference(hole)
    f.prism(surround,.07,.24,CARVED,'portal stone archivolt')
    f.prism(hole,-.55,-.49,DOOR,'deep entrance backing')
    for side in (-1,1):
        band(f,x+side*.52,1.36,.89,2.5,-.435,.07,GLASS,'paired entrance glazing')
        band(f,x+side*1.27,1.41,.26,2.66,.18,.39,CARVED,'portal jamb')
        band(f,x+side*1.27,2.74,.41,.17,.21,.45,CARVED,'portal capital')
        profile = ([(.05,.22),(.20,.22),(.27,.17),(2.46,.145),(2.52,.20),(2.70,.20)] if lod else
                   [(.05,.22),(.15,.22),(.18,.24),(.22,.24),(.27,.17),
                    (2.44,.145),(2.48,.18),(2.52,.20),(2.59,.19),(2.64,.22),(2.70,.22)])
        f.builder.lathe(f.point(x+side*1.18,0,.337)[:2],profile,CARVED,10 if lod else 20,'entry round stone column')

    band(f,x,2.87,2.95,.19,.18,.54,CARVED,'entry entablature')
    band(f,x,3.11,3.73,.115,.58,1.35,CANOPY,'flat entrance canopy')
    band(f,x,3.11,3.80,.15,1.26,.09,SASH,'canopy leading iron rail')
    for offset in ([-1.75,0,1.75] if lod else [-1.75,-.88,0,.88,1.75]):
        band(f,x+offset,3.125,.056,.107,.59,1.34,SASH,'canopy iron glazing bar')
    if not lod:
        for sign in [-1,1]:
            f.builder.tube([f.point(x+sign*1.60,3.14,1.17),f.point(x+sign*1.60,3.98,.07)],.027,SASH,6,'canopy suspension stay')
        for i in range(5):
            a=(i+1)*pi/6
            band(f,x+1.41*cos(a),3.16+.54*sin(a),.065,.16,.21,.10,SHADE,'arch stone joint')
    return hole


def add_building(b,lod):
    f=Facade(b,(-HALF,FACE),(HALF,FACE),'South street elevation')
    holes=[portal(f,x,lod)for x in PORTALS]
    for x in [-7.35,-4.95,-2.68,2.68,4.95,7.35]:
        holes.append(window(f,x,.66,1.44,2.48,lod,'ground sash'))
    tiers=[(4.75,2.68),(8.79,2.92),(12.62,2.82),(16.43,2.68),(20.57,1.73)]
    for i,(bottom,height) in enumerate(tiers):
        for x in CENTERS+WINGS:
            width=1.55 if x in CENTERS else 1.62
            holes.append(window(f,x,bottom,width,height,lod,'tier '+str(i+2)+' sash',i==1 and x in CENTERS))
            if x in CENTERS and i in (2,3):
                band(f,x,bottom+height+.10,width+.22,.15,.15,.31,CARVED,'window hood')
                if not lod:
                    for side in (-1,1):band(f,x+side*.57,bottom+height-.01,.13,.22,.14,.25,SHADE,'hood corbel')
    outline=box(-HALF,.04,HALF,23.33)
    f.wall(.04,23.33,holes,thickness=.54,material=FIELD)
    stone_courses(f,outline,holes,lod)
    for x in [-7.55,-5.,-2.5,0,2.5,5.,7.55]:
        band(f,x,14.08,.40,11.48,.115,.32,CARVED,'giant-order vertical pier')
        band(f,x,19.78,.56,.24,.15,.39,CARVED,'giant pier capital')
        if not lod:band(f,x,14.05,.21,10.98,.25,.068,ASHLAR,'pilaster raised face')
    for x in CENTERS:
        band(f,x,12.12,1.55,.68,.089,.18,CARVED,'window apron relief panel')
        roundel(f,x,12.12,lod)
        if not lod:
            for side in (-1,1):
                band(f,x+side*.62,12.12,.095,.47,.19,.085,SHADE,'raised apron edge')
    for z,height,projection in [(4.17,.20,.14),(8.21,.26,.19),(19.82,.20,.18),(22.92,.27,.27),(23.15,.24,.39)]:
        band(f,0,z,2*HALF+.10,height,projection,.44,CARVED,'continuous stone cornice')
    if not lod:
        for n in range(55):
            band(f,-14.46+n*.535,22.72,.18,.19,.29,.37,SHADE,'projecting cornice modillion')
    for side in (-1,1):
        x=side*11.56
        band(f,x,24.0,5.75,1.54,-.21,.49,ASHLAR,'end attic parapet')
        band(f,x,24.82,5.87,.18,-.19,.64,CARVED,'end parapet coping')
        for z in [23.60,24.35]:band(f,x,z,5.75,.105,-.015,.115,CARVED,'attic recessed panel course')
        oval=Point(x,24.14).buffer(.27,quad_segs=3 if lod else 9)
        f.prism(oval,.015,.13,CARVED,'end parapet shield boss')
    band(f,0,23.72,17.85,.83,-.40,.37,ASHLAR,'recessed central parapet')
    band(f,0,24.18,17.98,.11,-.36,.44,CARVED,'central parapet coping')
    for x in CENTERS:band(f,x,23.56,1.30,.18,-.177,.09,SHADE,'central parapet rectangular recess')
    band(f,0,7.99,7.10,.96,.28,.28,BOARD,'museum tablet')
    if lod:
        for char,glyph in lettering_shapes('上海电信博物馆',6.25,.61,font=FONT):
            simplified=glyph.simplify(.012,preserve_topology=True)
            f.prism(translate(simplified,yoff=7.99),.425,.455,GOLD,'museum name '+char)
    else:
        add_facade_lettering(f,'上海电信博物馆',0,7.99,6.25,.61,.425,.455,GOLD,label='museum name',font=FONT)
    b.box((0,(FACE+BACK)/2,.08),(2*HALF,BACK-FACE,.14),ASHLAR,label='stone threshold and plinth')
    b.box((0,(FACE+BACK)/2,23.34),(2*HALF,BACK-FACE,.16),ROOF,label='roof behind street cornice')
    b.box((0,BACK-.07,11.64),(2*HALF,.14,23.24),ASHLAR,label='plane of retained building')
    for x in [-HALF+.065,HALF-.065]:
        b.box((x,(FACE+BACK)/2,11.64),(.13,BACK-FACE,23.24),ASHLAR,label='short building return')
