"""The first regular bay east of the former bank's corner on Beijing East Road."""
from shapely.geometry import LineString, box
from shapely.ops import unary_union

from photo_architecture import Facade

TILE = 'weathered red face tile'
TILE_JOINT = 'thin red grey tile joint'
RUST = 'dark red pier course'
PALE = 'light stone facing'
SHADE = 'shadow in cut stone grooves'
TRIM = 'pale narrow ledges'
METAL = 'dark steel sash'
GLASS = 'smoky green grey glazing'
CAP = 'weathered grey cornice'
PALETTE = {key: {'color': color, 'roughness': roughness} for key,color,roughness in [
    (TILE,[.62,.35,.32],.93),(TILE_JOINT,[.49,.30,.28],.97),(RUST,[.41,.28,.27],.93),
    (PALE,[.79,.78,.71],.88),(SHADE,[.53,.53,.48],.94),(TRIM,[.83,.81,.73],.87),
    (METAL,[.22,.24,.22],.77),(GLASS,[.32,.39,.39],.42),(CAP,[.51,.52,.49],.90)]}
HALF=3.07580
DEPTH=.42
WINDOW_STARTS=[4.52,7.85,10.61,13.66]


def panel_moulding(f,shape,width,back,front,material,label):
    rim=shape.difference(shape.buffer(-width,join_style=2))
    f.prism(rim,back,front,material,label)


def large_lower_window(f):
    hole=box(-2.52,.16,2.52,2.96)
    f.prism(hole.buffer(.018,join_style=2),.105,.140,GLASS,'bottom window recessed glazing')
    panel_moulding(f,hole,.085,.18,.26,METAL,'lower steel outer frame')
    for x in [-1.53,-.51,.51,1.53]:
        f.box(x,1.56,.049,2.71,.075,.227,METAL,'five large lower window lights')
    f.box(0,2.01,4.99,.052,.085,.232,METAL,'large window horizontal transom')
    f.box(0,.14,5.16,.10,.36,.375,CAP,'bottom window sill')
    return hole


def triple_lights(f,bottom,height,level):
    holes=[]
    for i,x in enumerate([-1.72,0,1.72]):
        h=box(x-.635,bottom,x+.635,bottom+height);holes.append(h)
        f.prism(h.buffer(.015,join_style=2),.102,.136,GLASS,'level '+str(level)+' recessed glass')
        panel_moulding(f,h,.073,.155,.240,METAL,'level '+str(level)+' dark window joinery')
        f.box(x,bottom+height*.72,1.17,.050,.080,.206,METAL,'level '+str(level)+' sash transoms')
        f.box(x+.17,bottom+height*.86,.035,height*.215,.078,.207,METAL,'small upper sliding sash bars')
        f.box(x,bottom-.015,1.39,.073,.27,.363,TRIM,'pale projecting individual sills')
    return holes


def red_piers(f,lod):
    # Only the half piers bordering this single bay are retained. Columns have
    # red tile faces, small recessed bed joints and three wider grey floor bands.
    for side in [-1,1]:
        outer=side*HALF;inner=side*2.54
        lo,hi=sorted([outer,inner])
        f.prism(box(lo,.02,hi,15.80),.088,DEPTH+.032,TILE,'red tiled pier')
        if not lod:
            grooves=[]
            for r in range(1,118):
                z=r*.135
                if z>=15.75:break
                grooves.append(box(lo,z,hi,z+.008))
                middle=(lo+hi)/2+(.066 if r%2 else -.066)
                grooves.append(box(middle,z-.125,middle+.009,z-.013))
            f.prism(unary_union(grooves),DEPTH+.034,DEPTH+.041,TILE_JOINT,'small rectangular tile joints')
        for z in [3.28,6.88,9.96,12.78]:
            f.prism(box(lo,z,hi,z+.10),DEPTH+.035,DEPTH+.057,RUST,'dark horizontal pier bands')
        for z in [3.20,7.03,10.05,12.90]:
            f.prism(box(lo,z,hi,z+.042),DEPTH+.036,DEPTH+.064,CAP,'thin grey pier courses')


def double_fret(f,lod):
    # Two square panels, each comprising two opposed stepped turns connected by
    # a central descending stem. The grooves penetrate the pale face into a
    # darker stone bed, as in the oblique close view of the first structural bay.
    for cx in [-1.25,1.25]:
        field=box(cx-1.19,3.05,cx+1.19,4.30)
        f.prism(field,DEPTH+.01,DEPTH+.052,SHADE,'bank fret recess backing')
        traces=[]
        for side in [-1,1]:
            pts=[(.96,3.23),(.35,3.23),(.35,3.82),(.69,3.82),(.69,3.57),(.54,3.57)]
            traces.append(LineString([(cx+side*x,z)for x,z in pts]))
            pts=[(.03,3.22),(.03,3.92),(.83,3.92),(.83,3.45),(.48,3.45)]
            traces.append(LineString([(cx+side*x,z)for x,z in pts]))
        gaps=unary_union([l.buffer(.030,cap_style=2,join_style=2)for l in traces])
        f.prism(field.difference(gaps),DEPTH+.045,DEPTH+.105,PALE,'twin rectilinear carved frets')
        panel_moulding(f,field,.045,DEPTH+.094,DEPTH+.139,TRIM,'fret panel raised perimeter')
        if not lod:
            inner=field.buffer(-.092,join_style=2)
            panel_moulding(f,inner,.026,DEPTH+.104,DEPTH+.135,TRIM,'fine inset fret panel moulding')


def upper_bands(f,lod):
    for z,height,depth,material,label in [
        (3.0,.105,.52,TRIM,'lower fret shelf'),(4.36,.11,.49,TRIM,'upper fret band'),
        (13.22,.15,.54,TRIM,'upper window band sill'),(13.38,.12,.58,PALE,'upper band projecting lip'),
        (15.86,.18,.54,PALE,'cornice fascia'),(16.04,.17,.63,TRIM,'straight projecting eave'),
        (16.16,.082,.69,CAP,'flat cornice cap')]:
        f.box(0,z,2*HALF,height,depth-.09,(depth+.09)/2,material,label)
    # The repeated shallow rectangular frames below the top row of lights
    # can be read independently of the broader Greek-key ornament lower down.
    for x in [-2.36,-1.43,-.50,.43,1.36,2.29]:
        panel=box(x-.36,13.02,x+.36,13.34)
        panel_moulding(f,panel,.032,.54,.57,TRIM,'small top-band stepped squares')
        if not lod:
            f.box(x,13.06,.48,.025,.04,.576,TRIM,'inner lower line on top band')


def add_building(builder,lod):
    f=Facade(builder,(-HALF,0),(HALF,0),'Beijing bay')
    holes=[large_lower_window(f)]
    for level,(z,high) in enumerate(zip(WINDOW_STARTS,[2.16,1.92,1.86,1.88]),3):
        holes.extend(triple_lights(f,z,high,level))
    wall=box(-HALF,0,HALF,16.10).difference(unary_union(holes))
    f.prism(wall,.083,DEPTH,PALE,'pale wall with thirteen window openings')
    red_piers(f,lod)
    double_fret(f,lod)
    upper_bands(f,lod)
