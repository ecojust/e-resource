"""The stepped east front and short rear wings of Eddington House, 195 Changde Road."""
from pathlib import Path
import math
from shapely.geometry import Polygon, LineString, box
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

PLASTER='warm roughcast';TRIM='ivory balcony render';BRICK='umber spandrel brick'
LIGHT='brick joints';STONE='grey threshold';DARK='charcoal masonry band'
FRAME='umber window frames';GLASS='blue grey glazing';IRON='bronze rails';WOOD='door joinery'
SIGN='pale metal letters';GREEN='green number plate';ROOF='flat roof membrane'
PALETTE={k:dict(color=c,roughness=r,metallic=m)for k,c,r,m in [
    (PLASTER,[.69,.637,.535],.88,0),(TRIM,[.82,.776,.674],.75,0),
    (BRICK,[.402,.177,.118],.85,0),(LIGHT,[.54,.368,.266],.91,0),
    (STONE,[.42,.415,.386],.86,0),(DARK,[.251,.215,.192],.83,0),
    (FRAME,[.218,.190,.162],.58,.15),(GLASS,[.23,.302,.319],.27,.24),
    (IRON,[.26,.244,.212],.50,.42),(WOOD,[.254,.171,.122],.66,0),
    (SIGN,[.842,.827,.719],.42,.43),(GREEN,[.085,.284,.202],.48,.12),
    (ROOF,[.435,.423,.379],.91,0)]}
FONT=Path(__file__).parent/'fonts/EddingtonSign.otf'
LEVELS=[5.82,9.23,12.64,16.05,19.46,22.87]
TOP=26.82


def window(f,u,z,width,height,cols=3,rows=2,label='casements'):
    opening=box(u-width/2,z,u+width/2,z+height)
    f.window(opening,cols,rows,frame=FRAME,glass=GLASS,trim=False,label=label)
    f.box(u,z-.04,width+.14,.12,.22,.045,TRIM,label+' sill')


def balcony_plan(outer,y,r,lod):
    # Outer quadrant turns back into the end elevation. Inner end meets the middle pier.
    c=outer-r
    points=[(7.91,y),(c,y)]
    steps=8 if lod else 22
    for i in range(1,steps+1):
        t=-math.pi/2+math.pi*.5*i/steps
        points.append((c+r*math.cos(t),y+r+r*math.sin(t)))
    return points+[(outer,3.51),(7.91,3.51)]


def wing_deck(b,sign,level,z,lod):
    outside=[20.65,20.65,20.65,20.65,17.76,15.58][level]
    points=balcony_plan(outside,.02+.14*max(0,level-3),1.48,lod)
    poly=Polygon([(sign*x,y)for x,y in points])
    b.plan_prism(poly,z-.20,z,TRIM,'outer balconies/floor plates')
    line=LineString([(sign*x,y)for x,y in points[:-1]])
    wall=line.buffer(.115,cap_style=2,join_style=2)
    b.plan_prism(wall,z,z+.94,TRIM,'outer balconies/curving solid parapets')
    b.plan_prism(line.buffer(.14,cap_style=2,join_style=2),z+.93,z+1.02,PLASTER,'outer balconies/cappings')
    b.plan_prism(line.buffer(.122,cap_style=2,join_style=2),z-.17,z-.095,STONE,'outer balconies/underside drip')
    # A thin continuous rail sits above the curved parapet, with wide greenish panes behind it.
    path=[(sign*x,y,z+1.115)for x,y in points[:-1]]
    b.tube(path,.027,IRON,5 if lod else 8,'outer balconies/top rails')
    for i in range(5):
        x=sign*(8.04+(outside-1.54-8.04)*i/4)
        b.tube([(x,points[0][1],z+1.01),(x,points[0][1],z+1.115)],.018,IRON,5,'outer balconies/stanchions')


def long_wing(b,sign,lod):
    for i,z in enumerate(LEVELS):
        outside=[19.70,19.70,19.70,19.70,16.92,14.82][i]
        finish=LEVELS[i+1] if i<5 else 26.27
        a,bx=sorted((sign*7.73,sign*outside));y=2.52+max(0,i-3)*.34
        f=Facade(b,(a,y),(bx,y),'wing/living-room windows')
        span=bx-a
        bays=((-span*.245,span*.335),(span*.245,span*.335)) if span>7.5 else ((0,span*.71),)
        holes=[box(u-width/2,z+.54,u+width/2,z+2.77)for u,width in bays]
        f.wall(z-.02,finish,holes,.27,PLASTER)
        for u,width in bays:window(f,u,z+.54,width,2.23,4 if width>3.3 else 3,2,'living room glazing')
        depth=9.87-y
        if sign>0:end=Facade(b,(outside,y+.27),(outside,9.87),'north wing/return')
        else:end=Facade(b,(-outside,9.87),(-outside,y+.27),'south wing/return')
        side=box(-depth*.32,z+.65,-depth*.32+1.53,z+2.82)
        tall=box(depth*.04,z+.90,depth*.04+.63,z+2.66)
        end.wall(z-.03,finish,[side,tall],.23,PLASTER)
        for o,n in ((side,'return casement'),(tall,'vertical light')):
            u0,v0,u1,v1=o.bounds;window(end,(u1+u0)/2,v0,u1-u0,v1-v0,2,2,n)
        # The two levels above the short rear wings have a visible west face at the step.
        if i>=4:
            back=Facade(b,(bx,9.87),(a,9.87),'upper wing/rear enclosure')
            back.wall(z,finish,[],.24,PLASTER)
        wing_deck(b,sign,i,z,lod)
        # The roof beside each upper setback remains visible from the street.
        if i in (3,4,5):
            b.plan_prism(box(a,y,bx,9.89),finish-.15,finish+.02,ROOF,'wing/stepped flat roofs')
    # Two short rear wings enclose the shallow western recess described in the records.
    x0,x1=sorted((sign*8.2,sign*19.7))
    rear=Facade(b,(x1,13.04),(x0,13.04),'rear wing/outer wall')
    rear.wall(.04,19.45,[],.24,PLASTER)
    b.plan_prism(box(x0,9.77,x1,13.04),19.33,19.51,ROOF,'rear wing/flat roof')
    for x,orientation in [(x0,-1),(x1,1)]:
        y0,y1=9.86,12.81
        edge=Facade(b,(x,y0),(x,y1),'rear wing/east return') if orientation>0 else Facade(b,(x,y1),(x,y0),'rear wing/west return')
        edge.wall(.04,19.45,[],.24,PLASTER)


def core(b,lod):
    main=Facade(b,(-7.91,.10),(7.91,.10),'centre/east front')
    narrow=(-5.34,-3.48,3.48,5.34)
    openings=[]
    for i,z in enumerate(LEVELS):
        openings.extend(box(u-.586,z+.54,u+.586,z+2.77)for u in narrow)
        if i<4:openings.append(box(-1.39,z+.41,1.39,z+2.70))
    ground_lights=[box(u-.72,.64,u+.72,4.82)for u in (-5.41,-3.47,3.47,5.41)]
    portal=box(-2.13,.074,2.13,3.65)
    transom=box(-2.05,3.86,2.05,5.18)
    main.wall(.055,TOP,[*openings,*ground_lights,portal,transom],.26,PLASTER)
    # Four narrow red brick ribbons run without a break from the high lobby to the roof.
    # The exposed masonry surrounds the windows and extends into the upper parapet.
    for x in narrow:
        ribbon=box(x-.793,5.2,x+.793,26.72)
        for z in LEVELS:
            ribbon=ribbon.difference(box(x-.586,z+.54,x+.586,z+2.77))
        main.prism(ribbon,.004,.058,BRICK,'full height brick panels')
        spacing=.23 if not lod else .46
        for j in range(1,round(21.48/spacing)):
            z=5.2+j*spacing
            joints=ribbon.intersection(box(x-.793,z,x+.793,z+.014))
            if not joints.is_empty:
                main.prism(joints,.0585,.062,LIGHT,'masonry bed joints')
    for i,z in enumerate(LEVELS):
        for u in narrow:
            window(main,u,z+.54,1.172,2.23,2,2,'repeated vertical casement')
        if i<4:
            window(main,0,z+.41,2.78,2.29,3,2,'middle French window')
            b.box((0,-.51,z-.075),(5.93,1.39,.21),TRIM,label='middle/shallow balcony decks')
            balcony=Facade(b,(-2.96,-1.17),(2.96,-1.17),'middle/small balcony')
            wall=box(-2.96,z,2.96,z+.94)
            balcony.prism(wall,-.17,0,PLASTER,'front sill')
            for x in (-2.89,2.89):
                b.box((x,-.52,z+.47),(.14,1.28,.94),PLASTER,label='middle/shallow balcony side walls')
            balcony.box(0,z+.98,6.01,.10,.23,.035,TRIM,'parapet cap')
    # The high view shows a continuous pale central panel replacing the two upper balcony bays.
    # Slim bands step up on either side of the fin at the roof.
    main.prism(box(-1.56,19.35,1.56,27.42),.061,.13,PLASTER,'upper blank central pier')
    for width,high,front in [(1.73,27.77,.16),(1.28,28.10,.20),(.86,28.42,.24),(.41,28.72,.28)]:
        main.prism(box(-width/2,26.28,width/2,high),front-.044,front,TRIM,'stepped centre crown')
    for high in (26.52,26.78,27.04,27.30):
        for side in (-1,1):
            main.box(side*.508,high,.36,.085,.125,.269,STONE,'crown side notches')
    for u in (-6.89,-2.56,2.56,6.89):
        high=27.52 if abs(u)<3 else 27.09
        main.box(u,(high+5.09)/2,.337,high-5.09,.285,.09,TRIM,'raised facade piers')
    for u in (-5.41,-3.47,3.47,5.41):
        window(main,u,.64,1.44,4.18,2,5,'tall lobby lights')
    main.window(transom,4,2,FRAME,False,GLASS,'entry transom')
    # A recessed pair of doors and sidelights sit at the back of the striped entrance.
    glass=Facade(b,(-2.12,1.17),(2.12,1.17),'entry/doors')
    ap=box(-2.12,.11,2.12,3.63)
    glass.window(ap,4,2,frame=WOOD,glass=GLASS,trim=False,label='glazed entrance and sidelights')
    for u in (-.19,.19):
        glass.box(u,1.44,.048,.45,.067,-.091,IRON,'vertical door pulls')
    for side in (-1,1):
        x=side*2.28
        pillar=box(x-.25,-.68,x+.25,1.24)
        b.plan_prism(pillar,.07,3.65,TRIM,'entrance/striped jambs')
        for j in range(8):
            z=.28+j*.429
            b.plan_prism(pillar.buffer(.017,join_style=2),z,z+.17,DARK,'entrance/dark masonry courses')
    for i in range(3):
        b.box((0,-.59,3.61+.185*i),(5.46-.10*i,1.74-.15*i,.125),TRIM,label='entrance/three thin canopy slabs')
    sign=Facade(b,(-2.79,-1.13),(2.79,-1.13),'entrance/freestanding name')
    for x,char in zip((-1.87,-.62,.62,1.87),'常德公寓'):
        b.box((x,-1.14,4.08),(.074,.067,.34),IRON,label='name/metal supports')
        add_facade_lettering(sign,char,x,4.50,.72,.72,.018,.096,SIGN,label='current house name',font=FONT)
    sign2=Facade(b,(1.99,-.71),(2.57,-.71),'entrance/number')
    sign2.box(0,2.55,.48,.23,.042,.025,GREEN,'green 195 plate')
    add_facade_lettering(sign2,'195',0,2.555,.307,.136,.053,.068,SIGN,label='195',font=FONT)
    b.box((0,-.37,.072),(4.47,2.12,.12),STONE,label='entrance/raised threshold')
    b.plan_prism(box(-7.90,.12,7.90,9.85),TOP-.13,TOP+.08,ROOF,'central mass/roof')
    b.plan_prism(box(-7.91,9.60,7.91,9.90),TOP+.05,TOP+.48,PLASTER,'centre/rear parapet')
    for signx in (-1,1):
        x=signx*7.78
        b.box((x,5.0,TOP+.21),(.25,9.7,.43),PLASTER,label='centre/roof parapet returns')
    for signx in (-1,1):
        side=Facade(b,(signx*7.91,.36),(signx*7.91,9.64),'centre/upper return') if signx>0 else Facade(b,(signx*7.91,9.64),(signx*7.91,.36),'centre/upper return')
        side.wall(.08,TOP,[],.25,PLASTER)
    rear=Facade(b,(7.90,9.89),(-7.90,9.89),'centre/rear wall')
    rear.wall(.05,TOP,[],.25,PLASTER)


def street_base(b,sign):
    x0,x1=sorted((sign*7.91,sign*20.14))
    face=Facade(b,(x0,.77),(x1,.77),'wing/street floor and mezzanine')
    total=x1-x0
    centers=(-total*.28,0,total*.28)
    ground=[box(x-1.34,.29,x+1.34,2.91)for x in centers]
    mezz=[box(x-1.31,3.39,x+1.31,5.35)for x in centers]
    face.wall(.05,5.85,[*ground,*mezz],.34,PLASTER)
    for x in centers:
        window(face,x,.29,2.68,2.62,3,2,'street glazing')
        window(face,x,3.39,2.62,1.96,3,2,'mezzanine windows')
    for z in (.19,3.10,5.66):face.box(0,z,face.length+.10,.14,.26,.06,TRIM,'street sill band')
    outer=sign*20.14
    end=Facade(b,(outer,1.10),(outer,9.88),'end/ground storey') if sign>0 else Facade(b,(outer,9.88),(outer,1.10),'end/ground storey')
    end.wall(.05,5.83,[],.25,PLASTER)


def add_house(b,lod):
    core(b,lod)
    for sign in (-1,1):
        street_base(b,sign)
        long_wing(b,sign,lod)
    b.plan_prism(box(-20.13,.76,20.13,9.90),.014,.08,STONE,'building/ground floor')
    for sign in (-1,1):
        x0,x1=sorted((sign*8.2,sign*19.7))
        b.plan_prism(box(x0,9.76,x1,13.04),.012,.08,STONE,'rear wing/ground floor')
