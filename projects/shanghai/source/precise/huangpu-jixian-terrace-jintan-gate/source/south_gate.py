"""Editable masonry, inscription, lanterns and ironwork of the Jintan Road lane gate."""
from math import cos, pi, sin
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box

from photo_architecture import Facade
from sign_lettering import lettering_shapes
from shapely.affinity import translate

FONT = Path(__file__).parent / 'fonts' / 'JixianGateSign.otf'
STONE = 'Weathered pale grey render'
CAP = 'Warmer projecting stone moulding'
SHADOW = 'Cool recessed stone joint'
SOFFIT = 'Shaded underside of the lintel'
TABLET = 'Muted slate inscription tablet'
LETTER = 'Dark traditional inscription'
IRON = 'Black painted iron'
EDGE = 'Weathered iron highlights'
WOOD = 'Reddish brown plaque backing'
BRONZE = 'Dull brass plaque edging'
GLASS = 'Warm grey lantern glazing'
PALETTE = {
    name: {'color': colour, 'roughness': rough, 'metallic': metal}
    for name, colour, rough, metal in [
        (STONE,[.66,.63,.54],.91,0), (CAP,[.73,.70,.61],.86,0),
        (SHADOW,[.43,.42,.36],.95,0), (SOFFIT,[.54,.53,.46],.93,0),
        (TABLET,[.39,.40,.36],.83,.05), (LETTER,[.192,.19,.159],.79,.09),
        (IRON,[.096,.095,.089],.58,.47), (EDGE,[.175,.161,.139],.57,.39),
        (WOOD,[.28,.118,.067],.70,.12), (BRONZE,[.59,.43,.23],.45,.55),
        (GLASS,[.55,.54,.45],.35,.20),
    ]
}
OPEN_HALF = 1.60
PIER = .75
SPAN = OPEN_HALF + PIER
SPRING = 3.49
ARCH_TOP = 3.80
CROWN = 5.52


def arc(half, shoulder, crown, segments):
    """A shallow rubbed arch with a horizontal tangent at its midpoint."""
    return [(float(x), crown-(crown-shoulder)*(x/half)**2)
            for x in np.linspace(-half,half,segments+1)]


def band(face, curve, height, back, front, material, label):
    outline=Polygon(curve+[(x,z+height)for x,z in reversed(curve)])
    face.prism(outline,back,front,material,label)


def pier(face, side):
    u=side*(OPEN_HALF+PIER/2)
    face.box(u,2.47,PIER,4.94,.61,-.22,STONE,'Stone pier')
    face.box(u,.25,PIER+.075,.50,.65,-.205,STONE,'Plinth')
    face.box(u,.52,PIER+.13,.10,.72,-.195,CAP,'Plinth rim')
    face.box(u,2.88,PIER+.10,.09,.67,-.185,CAP,'Plaque head course')
    face.box(u,3.53,PIER+.13,.13,.71,-.19,CAP,'Spring block')
    face.box(u,3.63,PIER+.065,.071,.66,-.195,SHADOW,'Spring joint')
    face.box(u,4.94,PIER+.085,.095,.69,-.175,CAP,'Upper capital rim')
    face.box(u,5.06,PIER+.14,.16,.72,-.185,STONE,'Terminal cornice')
    face.box(u,5.18,PIER+.18,.10,.76,-.179,CAP,'Terminal coping')
    # The square recess contains a raised, stepped geometric bar on both piers.
    panel=box(u-.196,3.91,u+.196,4.59)
    face.prism(panel,.088,.113,SHADOW,'Recess behind stepped ornament')
    face.prism(panel.buffer(-.026),.112,.123,STONE,'Pale ornament ground')
    riser=Polygon([(u-.055,4.015),(u+.055,4.015),(u+.055,4.15),
                   (u+.105,4.15),(u+.105,4.205),(u+.055,4.205),
                   (u+.055,4.43),(u-.055,4.43),(u-.055,4.205),
                   (u-.102,4.205),(u-.102,4.15),(u-.055,4.15)])
    face.prism(riser,.123,.144,CAP,'Stepped relief on capital')
    # The smaller gilded wording varies between the dated source images.
    face.box(u,1.72,.565,2.09,.052,.126,WOOD,'Applied vertical plaque')
    edge=box(u-.2825,.675,u+.2825,2.765)
    face.prism(edge.difference(edge.buffer(-.012,join_style='mitre')),
               .150,.158,BRONZE,'Fine plaque border')
    for x in (u-.245,u+.245):
        for z in (.721,2.719):
            face.box(x,z,.022,.022,.012,.160,BRONZE,'Plaque corner fastenings')


def lamp(face, u, lod):
    z=3.155
    face.box(u,z+.13,.115,.13,.045,.118,IRON,'Lantern wall plate')
    builder=face.builder
    builder.tube([face.point(u,z+.12,.132),face.point(u,z+.22,.228),
                  face.point(u,z+.20,.306)],.020,IRON,5 if lod else 8,'Two wall lamp brackets')
    # Four facets taper below the glazed lantern. The rain cap has a separate overhang.
    for low,high,ra,rb,mat,tag in [
        (z-.20,z+.11,.056,.145,GLASS,'Tapered lantern glass'),
        (z+.11,z+.16,.180,.180,IRON,'Lantern eaves'),
        (z+.16,z+.235,.18,.044,IRON,'Lantern pyramidal cover')]:
        verts=[]
        for zz,rr in ((low,ra),(high,rb)):
            for a in (pi/4,3*pi/4,5*pi/4,7*pi/4):
                verts.append(face.point(u+rr*cos(a),zz,.286+rr*sin(a)))
        faces=[(0,3,2,1),(4,5,6,7)]+[(i,(i+1)%4,4+(i+1)%4,4+i)for i in range(4)]
        # Facade depth points south, reversing the horizontal rim orientation.
        builder.add(verts,[tuple(reversed(f)) for f in faces],mat,tag)
    for a in (pi/4,3*pi/4,5*pi/4,7*pi/4):
        builder.tube([face.point(u+.056*cos(a),z-.2,.286+.056*sin(a)),
                      face.point(u+.145*cos(a),z+.11,.286+.145*sin(a))],
                     .012,IRON,4 if lod else 6,'Four iron lantern ribs')


def masonry(face,lod):
    for side in (-1,1):
        pier(face,side)
        lamp(face,side*(OPEN_HALF+PIER/2),lod)
    n=15 if lod else 38
    lower=arc(OPEN_HALF,SPRING,ARCH_TOP,n)
    upper=arc(OPEN_HALF,5.12,5.40,n)
    face.prism(Polygon(lower+list(reversed(upper))),-.48,.015,STONE,'Curved crosshead')
    band(face,[(x,z-.008)for x,z in lower],.026,-.482,.022,SOFFIT,'Recessed arch soffit')
    for z,h,d,mat,label in [(0,.038,.061,SHADOW,'Cornice shadow'),(.032,.058,.094,CAP,'Curved string course'),(.088,.055,.116,STONE,'Head coping')]:
        band(face,[(x,y+z)for x,y in upper],h,-.50,d,mat,label)
    keystone=Polygon([(-.118,CROWN-.19),(.118,CROWN-.19),(.153,CROWN+.054),(-.153,CROWN+.054)])
    face.prism(keystone,-.035,.16,CAP,'Short central keystone')
    for u,character in zip((-.80,0,.80),'集賢邨'):
        panel=box(u-.24,4.38,u+.24,4.86)
        face.prism(panel,.018,.042,SHADOW,'Three square inscription reveals')
        face.prism(panel.buffer(-.013,join_style='mitre'),.041,.061,TABLET,'Inset inscription tablets')
        for _,ink in lettering_shapes(character,.34,.36,font=FONT):
            if lod:ink=ink.simplify(.0022,preserve_topology=True)
            face.prism(translate(ink,xoff=u,yoff=4.62),.061,.073,LETTER,'Name '+character)


def scroll(face,u,z,rx,rz,mirror,lod):
    pts=[]
    for f in np.linspace(0,1,10 if lod else 18):
        a=pi*(.18+1.63*f)
        pts.append(face.point(u+mirror*rx*(1-.78*f)*cos(a),z+rz*(1-.78*f)*sin(a),.018))
    face.builder.tube(pts,.0105,EDGE,4 if lod else 6,face.label+'/Scrolled ironwork')


def leaf(builder, west, lod):
    # In December 2021 the west gate spans the left half and the east gate folds inward.
    x=-OPEN_HALF+.052 if west else OPEN_HALF-.052
    side=1 if west else -1
    angle=np.radians(9 if west else 84)
    start=np.array([x,.275]);end=start+np.array([side*cos(angle),sin(angle)])*1.56
    # Point both facade normals into the visible street side.
    face=Facade(builder,start,end,'West iron gate'if west else'East iron gate')
    sign=1 if west else -1
    if not west:face=Facade(builder,end,start,'East iron gate')
    half=face.length*.5
    def height(u):return 2.65+.42*(.5+sign*u/face.length)
    for u in (-half+.027,half-.027):
        z=height(u);face.box(u,(z+.045)/2,.056,z-.045,.078,0,IRON,'Boundary stiles')
    for z,width in [(.12,.078),(.48,.039),(1.02,.045),(1.19,.064),(2.36,.047)]:
        face.box(0,z,face.length-.05,width,.055,0,IRON,'Horizontal rails')
    xs=np.linspace(-half+.030,half-.030,19 if lod else 31)
    for drop,r in [(0,.024),(.195,.017)]:
        builder.tube([face.point(u,height(u)-drop+.10*sin(pi*(u+half)/face.length),.0)for u in xs],r,IRON,5 if lod else 8,face.label+'/Arched crest rails')
    for col in range(1,12):
        u=-half+col*face.length/12;h=height(u)-.185+.10*sin(pi*(u+half)/face.length)
        face.box(u,(h+.105)/2,.020,h-.105,.031,0,IRON,'Vertical iron pickets')
        if not lod or col%2:
            for z in (.32,1.105,height(u)-.064):
                for direction in (-1,1):scroll(face,u+.020*direction,z,.042,.071,direction,lod)
    # The latch and hinge barrels are separate solids from the two moving frames.
    face.box(sign*(half-.10),1.14,.15,.096,.09,.033,EDGE,'Latch')
    for z in (.32,1.62,2.41):
        builder.tube([face.point(-sign*(half+.006),z-.062,0),face.point(-sign*(half+.006),z+.062,0)],.034,EDGE,6 if lod else 10,face.label+'/Hinges')


def gate(builder,lod):
    facade=Facade(builder,(-SPAN,0),(SPAN,0),'Jintan Road')
    masonry(facade,lod)
    for west in (True,False):leaf(builder,west,lod)
