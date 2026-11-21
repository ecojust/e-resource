"""Model the entered arch, recessed plaque, brick strips and two open street-facing leaves."""
from math import cos,pi,sin
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import LineString,Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import lettering_shapes
from stone_finish import texture_uv
from gate_roof import ROOF_MATERIALS,add_roof

HERE=Path(__file__).parent
GRANITE='dressed gate granite'
SEAM='weathered stone joints'
RIM='light cut granite'
SOFFIT='grey passage plaster'
PANEL='pale inscribed slab'
INK='oxide red inscription'
SHADOW='shadowed upper recess'
BRICK=('burnt red brick','rust brick','russet brick')
MORTAR='brick recess mortar'
LEAF='repainted red shutters'
TRIM='dark red joinery'
GLASS='shaded upper glass'
VENT='dark grey vent blades'
DATE='dark metal numerals'
METAL='aged bronze plaque'
GREEN='faded enamel green'
PALETTE={name:{'color':colour,'roughness':rough}for name,colour,rough in [
    (SEAM,[.32,.31,.285],.95),(RIM,[.64,.615,.56],.86),(SOFFIT,[.46,.455,.425],.92),
    (PANEL,[.80,.75,.635],.88),(INK,[.35,.058,.042],.66),(SHADOW,[.15,.139,.13],.96),
    (BRICK[0],[.51,.241,.15],.90),(BRICK[1],[.56,.258,.16],.89),(BRICK[2],[.47,.207,.139],.94),
    (MORTAR,[.54,.437,.348],.94),(LEAF,[.54,.17,.108],.61),(TRIM,[.29,.106,.078],.67),
    (GLASS,[.176,.212,.201],.35),(VENT,[.265,.275,.27],.61),(DATE,[.225,.20,.17],.58),
    (METAL,[.42,.355,.225],.61),(GREEN,[.25,.33,.26],.57)]}
PALETTE[GRANITE]={'color':[1,1,1],'roughness':.89,'texture':str(HERE/'stone-grain.png')}
PALETTE.update(ROOF_MATERIALS)
WIDTH=6.05
DEPTH=4.15
HALF_OPENING=1.91
SPRING=1.99
RISE=1.78
SHUTTER=box(-1.075,5.84,1.075,7.83)
LOUVRE=box(-.366,8.29,.366,10.68)
BRICK_WELLS=[box(x-.31,5.85,x+.31,9.54)for x in (-1.9,1.9)]
TOP_PROFILE=[(-3.025,10.96),(-1.39,10.96),(-1.39,12.27),(1.39,12.27),(1.39,10.96),(3.025,10.96)]
FONT=HERE/'fonts/ShangwenGateStudy.otf'

def arch(half,rise,steps):
    arc=[(half*cos(pi*i/steps),SPRING+rise*sin(pi*i/steps))for i in range(steps+1)]
    return Polygon([(-half,-.04),(half,-.04),*arc])

def sign(face,text,z,width,height,start,end,material,lod,label):
    for i,(char,shape)in enumerate(lettering_shapes(text,width,height,font=FONT)):
        outline=shape.simplify(.0019 if lod else .00085,preserve_topology=True)
        face.prism(translate(outline,yoff=z),start,end,material,f'{label} {i+1} {char}')

def lower_arch(face,lod):
    steps=22 if lod else 40
    inside=arch(HALF_OPENING,RISE,steps)
    outside=arch(HALF_OPENING+.15,RISE+.18,steps)
    # The curved intrados continues to the courtyard, with no crosswise base or closed back.
    rect=box(-WIDTH/2,0,WIDTH/2,5.83)
    face.prism(rect.difference(inside),-DEPTH,-.10,SOFFIT,'continuous arch vault')
    face.prism(rect.difference(outside),-.102,-.002,GRANITE,'street arch spandrel')
    rim=outside.difference(inside).intersection(rect)
    face.prism(rim,-.13,.032,RIM,'cut stone arch and uprights')
    outer_profile=arch(2.095,RISE+.22,steps)
    face.prism(outer_profile.difference(outside).intersection(rect),-.012,.016,SEAM,'arch edge shadow')
    for i in range(1,12):
        a=i*pi/12
        s0=((HALF_OPENING+.025)*cos(a),SPRING+(RISE+.021)*sin(a))
        s1=((HALF_OPENING+.144)*cos(a),SPRING+(RISE+.169)*sin(a))
        joint=LineString([s0,s1]).buffer(.006,cap_style='flat')
        face.prism(joint,.0323,.0345,SEAM,'radial arch joints')
    for side in (-1,1):
        pier=box(min(side*2.17,side*3.025),0,max(side*2.17,side*3.025),5.76)
        face.prism(pier,-.04,.045,GRANITE,'street edge pier')
        for z in [.19,1.05,2.15,3.47,4.62]:
            face.box(side*2.598,z,.845,.014,.01,.047,SEAM,'pier course')
        face.box(side*2.598,.087,.875,.174,.15,.025,RIM,'pier foot')
    # Adjustable civic signs change over time. Only their visible shapes are represented.
    for z,mat in [(1.03,METAL),(1.63,GREEN),(2.24,GREEN)]:
        face.box(2.55,z,.56,.27,.025,.051,mat,'east pier plaque')
    face.box(-2.60,1.24,.48,.34,.031,.054,METAL,'west pier plaque')
    # Framed sunk panel below the shutters. The outer line stands proud of its face.
    band=box(-2.13,4.15,2.13,5.785)
    recess=box(-1.25,4.53,1.25,5.46)
    face.prism(band.difference(recess),.004,.080,GRANITE,'wide plaque frieze')
    face.prism(recess,-.005,.027,SEAM,'deep plaque edge')
    slab=recess.buffer(-.077,join_style=2)
    glyphs=[(ch,translate(shape.simplify(.0019 if lod else .00085,preserve_topology=True),yoff=4.995))
            for ch,shape in lettering_shapes('邨門龍',1.92,.605,font=FONT)]
    # The 2019 street account identifies an intaglio inscription. Red pigment sits in the cuts.
    face.prism(slab.difference(unary_union([g for _,g in glyphs])),.024,.041,PANEL,'incised name slab')
    for char,glyph in glyphs:
        face.prism(glyph,.024,.033,INK,'incised red '+char)
    for z,w,h,d,mat in [(4.085,4.38,.070,.106,RIM),(4.150,4.36,.063,.083,GRANITE),
                          (5.76,4.43,.115,.158,RIM),(5.835,4.40,.045,.123,SEAM)]:
        face.box(0,z,w,h,d,d/2+.003,mat,'cornices around inscription')

def upper_wall(face,lod):
    upper=Polygon([(-WIDTH/2,5.83),(WIDTH/2,5.83),*reversed(TOP_PROFILE)])
    date_panel=box(-1.032,11.235,1.032,11.71)
    holes=[SHUTTER,LOUVRE,date_panel,*BRICK_WELLS]
    face.prism(upper.difference(unary_union(holes)),-.56,0,GRANITE,'upper stone with five recesses')
    face.prism(upper,-DEPTH,-.559,SOFFIT,'upper rear and side closure')
    for x,hole in zip((-1.9,1.9),BRICK_WELLS):
        face.prism(hole.buffer(.004,join_style=2),-.35,-.142,MORTAR,'brick pocket bed')
        left,bottom,right,top=hole.bounds
        for row in range(25):
            z=bottom+row*(top-bottom)/25
            for col in range(3):
                u=left+col*.37-(row%2)*.185
                b=box(u+.008,z+.009,u+.361,z+(top-bottom)/25-.009).intersection(hole)
                if b.area>.00045:face.prism(b,-.146,-.107,BRICK[(row*5+col+int(x>0))%3],'running bond in recess')
        face.box(x,9.535,.65,.065,.22,-.06,GRANITE,'stone head of brick recess')
    # Open red leaves reveal a set-back glazed transom and a dark central lower light.
    face.prism(SHUTTER.buffer(.005,join_style=2),-.547,-.519,SHADOW,'window recess')
    face.prism(box(-.99,5.94,.99,7.69),-.510,-.492,GLASS,'shaded window behind shutters')
    for x in (-.99,-.49,0,.49,.99):
        face.box(x,7.43,.040,.43,.085,-.454,TRIM,'window transom mullion')
    for z,h in [(5.92,.09),(7.16,.10),(7.68,.10)]:
        face.box(0,z,2.04,h,.087,-.45,TRIM,'red transom frame')
    for side in (-1,1):
        edge=side*1.037
        tip=side*.66
        plan=LineString([(edge,.025),(tip,.483)]).buffer(.038,cap_style='flat')
        face.builder.plan_prism(plan,5.92,7.72,LEAF,'upper window/open shutter '+str(side))
        for i in range(1,4):
            f=i/4
            u=edge+(tip-edge)*f
            y=.025+.458*f
            face.builder.box([u,y-.043,6.81],[.015,.016,1.69],TRIM,label='upper window/painted board joint')
    face.prism(LOUVRE.buffer(.003,join_style=2),-.43,-.414,SHADOW,'dark louvre recess')
    for i in range(20):
        z=8.33+i*.117
        # Wedge-sided blades leave gaps and shade the well.
        shape=Polygon([(.048,z+.068),(.177,z+.030),(.178,z+.046),(.048,z+.092)])
        face.builder.prism(shape,-.349,.349,lambda y,h,x:(x,y,h),VENT,'upper grille/sloped louvre blades')
    for x in (-.368,.368):
        face.box(x,9.48,.038,2.44,.1,-.053,RIM,'outer louvre reveal')
    hood=Polygon([(-.79,10.66),(-.79,10.75),(0,11.035),(.79,10.75),(.79,10.66),(0,10.88)])
    face.prism(hood,-.008,.094,RIM,'shallow peak over louvre')
    face.prism(date_panel,-.29,-.138,SEAM,'date pocket')
    face.prism(date_panel.buffer(-.044,join_style=2),-.141,-.095,GRANITE,'date panel face')
    sign(face,'1935',11.48,1.45,.282,-.094,-.061,DATE,lod,'year')
    for side in (-1,1):
        for z in [6.62,8.19,9.72,10.71]:
            face.box(side*2.625,z,.77,.012,.012,.002,SEAM,'upper outer pier course')
    for z,w in [(11.92,2.82),(12.16,2.84)]:
        face.box(0,z,w,.082,.23,.025,GRANITE,'stone band beneath high eaves')

def add_building(builder,lod):
    face=Facade(builder,[-WIDTH/2,0],[WIDTH/2,0],'street')
    lower_arch(face,lod)
    upper_wall(face,lod)
    add_roof(builder,lod)
    for part in builder.parts:
        if part['material']==GRANITE:
            uv=[texture_uv(*p)for p in part['vertices']]
            assert all(0<=u<=1 and 0<=v<=1 for u,v in uv)
            part['texcoords']=[(u,1-v)for u,v in uv]
