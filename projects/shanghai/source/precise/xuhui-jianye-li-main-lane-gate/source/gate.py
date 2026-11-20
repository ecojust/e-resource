"""Post-conversion street face of the two-window central lane gate at Jianye Li."""
from math import cos, pi, sin
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from sign_lettering import lettering_shapes

LIME='warm grey artificial stone'
LIGHT='pale moulded stone'
RECESS='shadowed stone joints'
WOOD='red timber sash'
GLASS='smoky window glass'
METAL='dark raised bronze'
BRASS='aged brown brass'
LETTERS='light brass inlay'
SHADE='shaded entrance stone'
HINGE='dark steel fittings'
PALETTE={
    LIME:{'color':[.57,.545,.50],'roughness':.88},
    LIGHT:{'color':[.68,.649,.583],'roughness':.85},
    RECESS:{'color':[.404,.389,.368],'roughness':.94},
    WOOD:{'color':[.386,.175,.137],'roughness':.69},
    GLASS:{'color':[.146,.166,.166],'metallic':.17,'roughness':.32},
    METAL:{'color':[.166,.205,.181],'metallic':.57,'roughness':.51},
    BRASS:{'color':[.36,.268,.159],'metallic':.49,'roughness':.54},
    LETTERS:{'color':[.73,.64,.46],'metallic':.43,'roughness':.44},
    SHADE:{'color':[.357,.347,.319],'roughness':.93},
    HINGE:{'color':[.20,.195,.176],'metallic':.45,'roughness':.62}
}
WIDTH=6.78
HALF=WIDTH/2
OPENING_WIDTH=5.52
SPRING=2.64
SOFFIT=2.83
DEPTH=1.54
WINDOW_CENTRES=(-.865,.865)
SILL=4.60
WINDOW_WIDTH=1.385
WINDOW_HEIGHT=1.075
FONT=Path(__file__).parent/'fonts/JianyeGateSigns.otf'


def silhouette():
    # The crown rises by successive horizontal offsets; the outer piers have their own caps.
    left=[(-HALF,0),(-HALF,6.57),(-3.22,6.57),(-3.22,6.74),(-2.73,6.74),
          (-2.73,6.40),(-2.23,6.40),(-2.23,6.63),(-1.53,6.63),(-1.53,7.03),
          (-.92,7.03),(-.92,7.29),(-.65,7.29),(-.65,7.41)]
    return Polygon(left+[( -x,z)for x,z in reversed(left)])


def portal():
    half=OPENING_WIDTH/2
    return Polygon([(-half,-.1),(half,-.1),(half,SPRING),(half-.47,SOFFIT),
                    (-half+.47,SOFFIT),(-half,SPRING)])


def upper_window(f,x,lod):
    left=x-WINDOW_WIDTH/2
    pane=box(left,SILL,left+WINDOW_WIDTH,SILL+WINDOW_HEIGHT)
    f.prism(pane,-.212,-.204,GLASS,'smoke glass')
    # Each of the two windows has three hinged leaves, each with two by three panes.
    leaves=[]
    for n in range(3):
        cell=box(left+n*WINDOW_WIDTH/3+.009,SILL+.012,
                 left+(n+1)*WINDOW_WIDTH/3-.009,SILL+WINDOW_HEIGHT-.012)
        inner=cell.buffer(-.043,join_style=2)
        sx=left+(n+.5)*WINDOW_WIDTH/3
        bars=[box(sx-.010,SILL,sx+.010,SILL+WINDOW_HEIGHT)]
        for j in [1,2]:
            z=SILL+WINDOW_HEIGHT*j/3
            bars.append(box(sx-.25,z-.012,sx+.25,z+.012))
        sash=cell.difference(inner.difference(unary_union(bars)))
        leaves.append(sash)
        if not lod:
            for height in (.14,.90):
                f.box(sx-.179,SILL+height,.024,.062,.026,-.053,HINGE,'casement hinges')
    f.prism(unary_union(leaves),-.124,-.064,WOOD,'three timber casements')
    f.prism(pane.buffer(.042,join_style=2).difference(pane),-.168,-.025,WOOD,'timber frame')
    f.box(x,SILL-.056,WINDOW_WIDTH+.12,.09,.176,.002,LIGHT,'window sill')


def fret(f,lod):
    # A continuous angular fret sits beneath a row of individual dentils.
    length=5.83
    f.box(0,4.125,length,.235,.064,.040,RECESS,'recess below fret')
    count=28
    pitch=length/count
    segments=[]
    for i in range(count):
        x=-length/2+i*pitch
        outline=[(x,4.069),(x+pitch*.27,4.069),(x+pitch*.27,4.181),
                 (x+pitch*.75,4.181),(x+pitch*.75,4.091),(x+pitch*.54,4.091),
                 (x+pitch*.54,4.143)]
        segments.append(LineString(outline).buffer(.0175,cap_style=2,join_style=2))
    f.prism(unary_union(segments),.068,.118,LIGHT,'interlocking square fret')
    f.box(0,3.996,length+.08,.061,.144,.052,LIGHT,'frieze lower fillet')
    f.box(0,4.259,length+.12,.073,.17,.065,LIGHT,'frieze ledge')
    for i in range(50):
        x=-length/2+(i+.5)*length/50
        f.box(x,4.34,.076,.113,.136,.057,LIGHT,'individual dentils')
    f.box(0,4.425,length+.10,.078,.164,.051,LIGHT,'dentil cornice')


def stonework(f,surface):
    # Narrow joints across the original large panels stay off the names, trim and openings.
    for z in (.47,1.04,1.56,2.18,3.07,3.82,4.52,5.87,6.225):
        joint=surface.intersection(box(-HALF+.07,z-.006,HALF-.07,z+.006))
        f.prism(joint,.004,.009,RECESS,'fine horizontal stone joint')
    for side in (-1,1):
        x=side*3.105
        f.box(x,.095,.62,.19,.26,.085,LIGHT,'plinth foot')
        f.box(x,.225,.56,.085,.205,.066,LIME,'plinth ledge')
        f.box(x,1.55,.442,2.55,.134,.055,LIME,'outer stone pier')
        f.box(x,5.065,.403,1.30,.124,.046,LIME,'upper architrave pier')
        for z,width,height,depth in [(5.78,.49,.08,.145),(5.89,.53,.11,.17),
                                    (6.03,.57,.082,.21),(6.50,.51,.063,.14)]:
            f.box(x,z,width,height,depth,.078,LIGHT,'outer pier capital')
        # Paired rectangular sunk panels flank the casements.
        px=side*2.18
        outer=box(px-.50,4.55,px+.50,5.75)
        f.prism(outer,.009,.028,RECESS,'panel inner shadow')
        f.prism(outer.buffer(-.039,join_style=2),.031,.047,LIME,'recessed smooth panel')
        f.prism(outer.buffer(.041,join_style=2).difference(outer),.023,.079,LIGHT,'panel raised frame')
    for z,w,h,d in [(5.91,5.88,.058,.114),(6.005,5.97,.103,.189),(6.145,5.87,.057,.124),
                     (6.67,3.12,.078,.14),(7.03,2.98,.054,.129),(7.305,1.94,.064,.139),
                     (7.413,1.38,.062,.162)]:
        f.box(0,z,w,h,d,.054,LIGHT,'stepped parapet profiles')


def lettering(f,text,z,width,height,back,front,material,lod):
    for number,(char,shape) in enumerate(lettering_shapes(text,width,height,font=FONT),1):
        if lod:
            shape=shape.simplify(.0023 if width>1 else .0008,preserve_topology=True)
        f.prism(translate(shape,yoff=z),back,front,material,f'lettering {number} {char}')


def add_gate(builder,lod=False):
    front=Facade(builder,(-HALF,0),(HALF,0),'Main gate')
    upper=[box(x-WINDOW_WIDTH/2,SILL,x+WINDOW_WIDTH/2,SILL+WINDOW_HEIGHT) for x in WINDOW_CENTRES]
    body=silhouette().difference(unary_union([portal(),*upper]))
    front.prism(body,-.40,0,LIME,'street front with two windows and open portal')
    # Returns represent the visible recessed passage. Its rear remains the existing city volume.
    for s in [-1,1]:
        x=s*(HALF+OPENING_WIDTH/2)/2
        builder.box([x,(DEPTH+.396)/2,SPRING/2],[(WIDTH-OPENING_WIDTH)/2,DEPTH-.396,SPRING],
                    SHADE,label='Inner entrance pier and jamb')
    front.prism(box(-HALF,SPRING,HALF,SOFFIT+.16).difference(portal()),-DEPTH,-.396,
                SHADE,'recessed portal soffit')
    front.prism(silhouette().intersection(box(-HALF,SOFFIT+.16,HALF,7.5)).difference(unary_union(upper)),
                -DEPTH,-.396,LIME,'upper gate return')
    for x in WINDOW_CENTRES:upper_window(front,x,lod)
    stonework(front,body)
    fret(front,lod)
    if not lod:
        arch=portal().buffer(.046,join_style=2).difference(portal())
        front.prism(arch.intersection(box(-HALF,.18,HALF,SOFFIT+.09)),.012,.058,LIGHT,'entrance arris')
    lettering(front,'建業里總衖',3.462,3.82,.435,.023,.113,METAL,lod)
    front.box(0,3.035,2.08,.352,.080,.055,BRASS,'modern bronze sign')
    front.prism(box(-1.01,2.883,1.01,3.187).buffer(-.016,join_style=2).boundary.buffer(.009,join_style=2),
                .096,.109,BRASS,'bronze plaque border')
    lettering(front,'CAPELLA',2.983,.718,.103,.096,.108,LETTERS,lod)
    # A small star is clear above the hotel's plain lettering in the February 2020 close photograph.
    star=Polygon([((.044 if j%2==0 else .019)*sin(j*pi/8),
                   3.117+(.044 if j%2==0 else .019)*cos(j*pi/8))for j in range(16)])
    front.prism(star,.097,.110,LETTERS,'small tablet star')
