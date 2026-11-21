"""East Bund elevation of the former Yangtze Insurance Association at number 26."""
from pathlib import Path
import math
from shapely.geometry import Point, Polygon, box as rect
from photo_architecture import PALETTE as COMMON, Facade, opening
from sign_lettering import add_facade_lettering

WIDTH = 18.50
AXES = (-6.07, -2.52, 0., 2.52, 6.07)
STONE = 'limestone'
CARVED = 'carved pale stone'
DARK = 'bronze window frame'
IRON = 'wrought iron'
GLASS = 'recessed glass'
GRANITE = 'stone base courses'
DOOR = 'recessed entrance joinery'
BRAND = 'painted sign enamel'
PALETTE = {**COMMON, GRANITE:{'color':[.54,.52,.47],'roughness':.89},
           DOOR:{'color':[.18,.153,.105],'roughness':.63},
           BRAND:{'color':[.058,.25,.216],'roughness':.52}}
FONT = Path(__file__).parent/'fonts/YangtzeBankLetters.otf'


def horizontal(builder, x, y, z, width, depth, height, material, label):
    builder.box((x,y,z),(width,depth,height),material,label=label)


def framed_openings(wall, lo, hi, windows, material, lod):
    cuts = [(opening(x,z,width,height,arch,segments=8 if lod else 16),name)
            for x,z,width,height,arch,name in windows]
    wall.wall(lo,hi,[profile for profile,_ in cuts],thickness=.36,material=material)
    for profile,name in cuts:
        door = 'street doorway' in name
        wall.window(profile,1 if door else 2,2 if lod else 3,
                    frame=DARK,glass=DOOR if door else GLASS,trim=False,label=name)
        if not lod and 'arch' in name:
            trim=profile.buffer(.115,join_style=2).difference(profile)
            wall.prism(trim,.018,.145,CARVED,name+' architrave')


def dressed_arch(wall,x,lod):
    # Visible wedge joints fan out from the spring of every second-storey arch.
    spring=9.18
    count=7 if lod else 11
    for i in range(count):
        angle0=i*math.pi/count+.014
        angle1=(i+1)*math.pi/count-.014
        outer=1.09 if i==count//2 else 1.005
        points=[(x+radius*math.cos(angle),spring+radius*math.sin(angle))
                for radius,angle in ((.871,angle0),(outer,angle0),(outer,angle1),(.871,angle1))]
        wall.prism(Polygon(points),.145,.202 if i==count//2 else .176,CARVED,'rusticated arch voussoir')
    if not lod:
        for angle in (math.pi/4,math.pi/2,3*math.pi/4):
            wall.line((x,spring,-.143),(x+.75*math.cos(angle),spring+.75*math.sin(angle),-.143),
                      .029,DARK,6,'fanlight glazing bars')


def upper_garland(wall,x,compact):
    # The daylight elevation shows a round head and a shallow symmetrical swag
    # high on the giant pilasters. Only these visible forms are resolved.
    roundel=Point(x,24.74).buffer(.23,quad_segs=5 if compact else 9)
    wall.prism(roundel,.257,.34,CARVED,'upper pier roundel')
    if not compact:
        for direction in (-1,1):
            points=[(x+direction*(.03+.42*t),24.39-.22*math.sin(t*math.pi),.26)
                    for t in (0,.25,.5,.75,1)]
            wall.builder.tube([wall.point(*v)for v in points],.051,CARVED,7,'shallow carved garland')


def iron_rail(wall, mid, width, bottom, height, depth, lod, label):
    for h in (.11,height):
        wall.box(mid,bottom+h,width,.078,.076,depth,IRON,label+' horizontal rail')
    count=max(2,round(width/(.47 if lod else .27)))
    for i in range(count+1):
        u=mid-width/2+i*width/count
        wall.box(u,bottom+height/2,.044,height,.055,depth,IRON,label+' upright')


def attic_parapet(wall, x, width, z, lod):
    for h in (.08,.50):
        wall.box(x,z+h,width,.11,.18,.095,CARVED,'upper terrace coping')
    count=max(2,round(width/.69))
    for i in range(count):
        left=x-width/2+i*width/count
        right=left+width/count
        wall.line((left,z+.12,.095),(right,z+.46,.095),.045,CARVED,4,'stone lattice')
        if not lod:
            wall.line((left,z+.46,.095),(right,z+.12,.095),.045,CARVED,4,'stone lattice')


def lower_and_middle(builder, front, lod):
    openings=[]
    for j,x in enumerate(AXES):
        side=j in (0,4)
        openings.append((x,.14,2.44 if side else 1.63,3.94 if side else 4.38,0,
                         'street doorway '+str(j) if side else 'ground-floor central window '+str(j)))
        openings.append((x,6.10,1.69,3.91,.83,'rusticated arched bay '+str(j)))
    framed_openings(front,.02,11.24,openings,GRANITE,lod)
    # Actual horizontal joints stop at the five arches and two entrance surrounds.
    for z in (.75,1.52,2.34,3.12,3.95,4.73,6.20,6.94,7.68,8.42,9.16,9.90,10.65):
        band=rect(-WIDTH/2,z-.025,WIDTH/2,z+.025)
        for x,base,w,h,a,_ in openings:
            if base<z+.04 and z-.04<base+h:
                band=band.difference(opening(x,base,w+.13,h+.07,a,segments=8))
        front.prism(band,.012,.037,'dark stone','rusticated joint')
    for x in AXES:
        dressed_arch(front,x,lod)
    for x in (AXES[0],AXES[-1]):
        for dx in (-1.38,1.38):
            front.box(x+dx,2.03,.36,4.05,.34,.03,CARVED,'street portal jamb')
        front.box(x,4.19,3.15,.29,.43,.08,CARVED,'street portal lintel')
    for z,h,proj in ((5.50,.25,.51),(5.73,.18,.64),(11.12,.25,.31),(11.38,.16,.34)):
        front.beam(z,h,proj,CARVED,label='ground and second storey cornices')
    iron_rail(front,0,17.83,5.82,.94,.44,lod,'continuous first-floor balcony')
    # Each of the three upper storeys has five axes. The upper axis has a round-headed top light.
    middle=[]
    for j,x in enumerate(AXES):
        for level,bottom in enumerate((12.01,16.73,21.30)):
            middle.append((x,bottom,1.65,3.45 if level<2 else 2.88,.79 if level==2 else 0,
                           f'main tier {level+3} '+('arched ' if level==2 else '')+f'window {j+1}'))
    framed_openings(front,11.24,25.83,middle,STONE,lod)
    for x in (-8.68,-4.39,4.39,8.68):
        front.box(x,18.28,.62,13.70,.37,.06,STONE,'high pilaster shaft')
        front.box(x,11.62,.78,.34,.46,.10,CARVED,'pilaster foot')
        front.box(x,24.91,.94,.56,.45,.09,CARVED,'pilaster capital')
        upper_garland(front,x,lod)
    for z,h,proj in ((24.99,.15,.23),(25.45,.30,.45),(25.81,.26,.74),(26.08,.17,.85)):
        front.beam(z,h,proj,CARVED,label='projecting fifth-storey cornice')
    for i in range(16 if lod else 31):
        n=15 if lod else 30
        front.box(-8.72+i*17.44/n,25.25,.20,.24,.46,.12,CARVED,'cornice modillion')
    # The carved central panel above the row of arches is represented by its visible moulding.
    panel=opening(0,10.20,2.60,1.73,1.03,segments=12)
    front.prism(panel,.06,.17,CARVED,'raised central arch-head panel')
    front.prism(panel.buffer(-.14).boundary.buffer(.045),.17,.22,STONE,'cartouche rim')
    add_facade_lettering(front,'中国农业银行',.50,20.40,5.54,.72,.035,.10,DARK,
                        label='contemporary bank lettering',font=FONT)
    mark=Point(-2.94,20.40).buffer(.46,quad_segs=8).difference(Point(-2.94,20.40).buffer(.32,quad_segs=8))
    front.prism(mark,.042,.11,BRAND,'circular enamel bank sign')
    front.box(-2.94,20.40,.08,.46,.08,.075,BRAND,'bank emblem stem')


def upper_storeys(builder, ledger, lod):
    # Set back between the outer pavilions, each shaft pair frames one of the three gallery openings.
    gallery=Facade(builder,(-3.23,2.25),(3.23,2.25),'sixth-storey gallery back')
    framed_openings(gallery,26.1,29.52,[(x,26.43,1.52,2.73,0,'gallery rear window')for x in (-2.13,0,2.13)],STONE,lod)
    for x in (-1.52,-1.05,1.05,1.52):
        builder.lathe((x,.41),[(26.16,.196),(26.28,.215),(26.42,.157),(28.87,.130),
                      (29.02,.19),(29.17,.23),(29.30,.23)],CARVED,8 if lod else 14,'paired Ionic shaft')
        if not lod:
            for side in (-1,1):
                center=x+side*.172
                path=[(center+.087*math.cos(i*math.pi/8),.172,29.08+.087*math.sin(i*math.pi/8))for i in range(17)]
                builder.tube(path,.043,CARVED,6,'Ionic capital scroll')
    horizontal(builder,0,1.92,26.10,WIDTH,3.63,.24,CARVED,'sixth-storey gallery floor')
    horizontal(builder,0,1.92,29.59,WIDTH,3.63,.34,CARVED,'gallery ceiling and terrace')
    for sign in (-1,1):
        center=sign*6.18
        a,b=(center-2.92,.27),(center+2.92,.27)
        outer=Facade(builder,a,b,'sixth-storey side pavilion')
        framed_openings(outer,26.09,29.61,[(0,26.56,1.66,2.21,0,'paired lights below attic')],STONE,lod)
        iron_rail(outer,0,2.22,26.20,.83,.21,lod,'pavilion railing')
        for sx in (-1,1):
            horizontal(builder,center+sx*2.87,1.86,27.81,.16,3.24,3.48,STONE,'pavilion return at terrace')
    ledger.beam(29.70,.25,.50,CARVED,label='terrace entablature')
    attic_parapet(ledger,0,WIDTH-.10,29.85,lod)
    back=Facade(builder,(-3.53,2.91),(3.53,2.91),'set-back middle attic')
    framed_openings(back,29.77,32.68,[(x,30.46,1.42,1.64,0,'middle attic window') for x in (-2.27,0,2.27)],STONE,lod)
    horizontal(builder,0,3.05,32.71,7.13,.79,.16,'roof zinc','middle attic roof coping')
    iron_rail(back,0,6.92,32.77,.57,.14,lod,'upper middle rails')
    for sign in (-1,1):
        x=sign*6.13
        front=Facade(builder,(x-2.69,.64),(x+2.69,.64),'roof pavilion')
        framed_openings(front,29.78,33.65,[(0,30.42,2.93,2.77,0,'large divided attic window')],STONE,lod)
        for h,w,dep in [(33.51,5.52,3.28),(33.76,5.69,3.47),(33.98,5.45,3.35)]:
            horizontal(builder,x,2.08,h,w,dep,.21,CARVED,'attic eave and shoulder')
        for sx in (-1,1):
            horizontal(builder,x+2.62*sx,2.05,31.63,.17,2.80,3.73,STONE,'short attic pavilion return')
        iron_rail(front,0,4.92,34.10,.66,-.10,lod,'attic guard rail')
    builder.tube([(0,2.47,32.75),(0,2.47,37.92)],.044,IRON,6 if lod else 10,'central flagstaff')


def add_yangtze(builder,lod):
    front=Facade(builder,(-WIDTH/2,0),(WIDTH/2,0),'Bund east facade')
    lower_and_middle(builder,front,lod)
    for side in (-1,1):
        horizontal(builder,side*(WIDTH/2-.10),1.74,12.95,.18,3.45,25.87,STONE,'short closure of facade section')
    horizontal(builder,0,1.78,.085,WIDTH-.12,3.46,.13,GRANITE,'ground-floor threshold slab')
    upper_storeys(builder,front,lod)
