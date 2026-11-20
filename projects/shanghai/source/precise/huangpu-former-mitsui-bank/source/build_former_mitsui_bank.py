"""Author the photo-documented south colonnade of the former Mitsui Bank, 50 Jiujiang Road."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from photo_architecture import Facade, opening
from sign_lettering import add_facade_lettering

P = json.loads((HERE / 'parameters.json').read_bytes())
META = {
    'id': P['id'],
    'name': '上海公库（原三井银行九江路正门与六柱廊）',
    'status': 'photo-informed-partial-exterior',
    'scope': 'The south street entrance and six-column stone front of the former Mitsui Bank, 50 Jiujiang Road.',
    'model_scope_zh': '九江路50号中央双扇金属门、上方铁花、两旁长格栅及石壁画框、上部两两成组的六柱廊和深檐。记录2015年可见的建设银行招牌。背部天井与临街两端保留城市原景。',
    'viewer_page': 'former-mitsui-bank.html',
    'audit_directory': 'data/audit/former-mitsui-bank-v1/',
    'coordinate_convention': 'glTF X along the south front toward the east-northeast, Y up, Z toward Jiujiang Road.',
    'source_register': 'source/precise/' + P['id'] + '/reference-review.json',
    'map_reference_license': 'OpenStreetMap and Overture Maps, ODbL-1.0.',
    'interiors_modeled': False,
}
MATERIALS = {
    'granite ashlar': ([.52,.49,.45], .88, 0),
    'carved granite': ([.61,.575,.515], .85, 0),
    'recessed stone': ([.435,.415,.39], .93, 0),
    'plinth stone': ([.376,.365,.343], .89, 0),
    'stone joint': ([.37,.345,.315], .90, 0),
    'glass': ([.213,.258,.273], .31, .23),
    'sash': ([.145,.147,.14], .57, .35),
    'bronze iron': ([.145,.127,.100], .53, .56),
    'raised bronze': ([.244,.210,.157], .48, .64),
    'dark backing': ([.094,.097,.094], .65, .17),
    'blue enamel': ([.043,.19,.49], .42, .14),
    'white enamel': ([.826,.841,.819], .42, .11),
    'sign letters': ([.116,.121,.120], .54, .12),
    'roof coping': ([.350,.348,.323], .85, .04),
}
PALETTE = {k:{'color':c,'roughness':r,'metallic':m} for k,(c,r,m) in MATERIALS.items()}
COLUMN_X = [-10.08,-5.27,-3.62,3.62,5.27,10.08]
WINDOW_X = [-8.79,-7.05,-1.72,0.,1.72,7.05,8.79]
WINDOW_Z = [9.48,12.74,16.0,19.26]
FONT = HERE / 'fonts' / 'BankLettering.otf'
HALF = P['street_section_width_m']/2
BACK = P['street_section_depth_m']


def ring(f, shape, amount, back, front, material, label):
    inner = shape.buffer(-amount, join_style='mitre')
    f.prism(shape.difference(inner), back, front, material, label)


def octagon(u,z,w,h,cut=.22):
    a,b=w/2,h/2
    c=min(w,h)*cut
    return Polygon([(u-a+c,z-b),(u+a-c,z-b),(u+a,z-b+c),(u+a,z+b-c),
                    (u+a-c,z+b),(u-a+c,z+b),(u-a,z+b-c),(u-a,z-b+c)])


def ashlar(f, outline, cavities, gap=.020):
    """The granite has large dressed blocks. Grooves stop at each real aperture."""
    face=outline.difference(unary_union(cavities))
    x0,z0,x1,z1=outline.bounds
    strips=[]
    for k,z in enumerate(np.arange(z0+.84,z1,.84)):
        strips.append(box(x0,z-gap/2,x1,z+gap/2))
        for x in np.arange(x0+1.05+(k%2)*.92,x1,1.84):
            strips.append(box(x-gap/2,z-.84,x+gap/2,z))
    f.prism(face.intersection(unary_union(strips)), .001,.009,'stone joint','fine granite joints')


def glass(f,x,z):
    aperture=opening(x,z,1.04,1.64)
    f.prism(aperture.buffer(.012,join_style='mitre'),-.39,-.35,'glass','recessed panes')
    ring(f,aperture,.057,-.32,-.225,'sash','window reveal frame')
    f.box(x,z+1.06,1.03,.048,.095,-.235,'sash','sash transom')
    f.box(x,z-.025,1.13,.072,.21,-.028,'carved granite','cut sill')


def chamfered_column(b,x):
    """Cut-corner shaft and the angular cap shapes visible in the original photograph."""
    y=1.24
    footprint=octagon(x,y,1.36,1.30,.20)
    b.plan_prism(octagon(x,y,1.47,1.41,.19),9.07,9.32,'carved granite','Colonnade/bottom course')
    b.plan_prism(footprint,9.32,21.74,'granite ashlar','Colonnade/chamfered shaft')
    # The narrow straight masonry divisions continue vertically over multiple drums.
    for dx in [-.34,0.,.34]:
        b.box((x+dx,y-.652,15.53),(.015,.009,12.39),'stone joint',label='Colonnade/vertical shaft joints')
    for z in [11.85,14.4,16.96,19.51]:
        b.plan_prism(footprint.buffer(.0018,join_style='mitre'),z,z+.010,'stone joint','Colonnade/drum beds')
    b.plan_prism(octagon(x,y,1.44,1.36,.18),21.73,21.84,'recessed stone','Colonnade/capital neck')
    b.plan_prism(octagon(x,y,1.53,1.46,.16),21.84,22.69,'carved granite','Colonnade/cut capital')
    b.plan_prism(octagon(x,y,1.61,1.52,.13),22.69,22.83,'carved granite','Colonnade/abacus')
    front=Facade(b,[x-.62,y-.731],[x+.62,y-.731],'Cap')
    # The frontal face shows a squat cut-corner boss with a recessed lower edge.
    front.prism(octagon(0,22.26,.72,.30,.28),.002,.092,'granite ashlar','angular frontal boss')
    front.prism(Polygon([(-.32,22.22),(.32,22.22),(.23,22.12),(-.22,22.12)]),.095,.119,'recessed stone','under boss rebate')
    pts=list(octagon(x,y,1.53,1.46,.16).exterior.coords)
    # Quarter disks just below the top course turn the ornament around each chamfer.
    for a,e in zip(pts,pts[1:]):
        if .26<math.dist(a,e)<.5:
            face=Facade(b,a,e,'Cap corner')
            rim=Polygon([(-.15,22.63),(.15,22.63),(.12,22.54),(.063,22.49),(-.063,22.49),(-.12,22.54)])
            face.prism(rim,.003,.058,'granite ashlar','drop carving')


def central_doors(f,lod):
    for sign in [-1,1]:
        x=sign*1.00
        leaf=box(x-.98,.20,x+.98,5.09)
        f.prism(leaf,-.58,-.47,'bronze iron','paired door leaves')
        ring(f,leaf,.105,-.46,-.387,'raised bronze','leaf perimeter')
        for z,w,h in [(1.14,1.30,1.48),(2.66,1.27,1.27),(4.12,1.30,1.45)]:
            shape=octagon(x,z,w,h,.23)
            ring(f,shape,.105,-.47,-.315,'raised bronze','octagonal panel moulding')
            ring(f,shape.buffer(.10,join_style='mitre'),.034,-.46,-.360,'bronze iron','outer octagon trim')
            if z==2.66:
                # Raised central convex boss is an ellipse on the door face.
                from shapely.geometry import Point
                boss=affinity.scale(Point(x,z).buffer(1,quad_segs=8 if lod else 13),.36,.42,origin=(x,z))
                f.prism(boss,-.46,-.30,'bronze iron','central convex boss')
                ring(f,boss.buffer(.055),.043,-.45,-.276,'raised bronze','oval escutcheon ring')
        for side in [-1,1]:
            for z in np.arange(.39,4.99,.27 if lod else .145):
                f.prism(octagon(x+side*.85,z,.055,.071),-.40,-.31,'raised bronze','leaf border beads')
        for z0,z1 in [(1.88,2.05),(3.29,3.48)]:
            for dx in [-.62,0,.62]:
                f.prism(octagon(x+dx,(z0+z1)*.5,.14,z1-z0),-.45,-.34,'raised bronze','panel separator studs')
    f.box(0,5.38,4.18,.51,.22,-.38,'bronze iron','number lintel')
    add_facade_lettering(f,'50',0,5.39,.40,.24,-.265,-.209,'raised bronze',font=FONT,label='street number')


def grille(f,x,z,w,h,side,lod):
    sh=opening(x,z,w,h)
    f.prism(sh.buffer(.01,join_style='mitre'),-.60,-.56,'dark backing','shadow behind iron')
    ring(f,sh,.125,-.43,-.31,'bronze iron','perimeter of grille')
    cells=4 if side else 3
    ustep=(w-.36)/(1 if side else cells)
    hstep=(h-.35)/(cells if side else 1)
    for j in range(cells if side else 1):
        for i in range(1 if side else cells):
            u=x-w/2+.18+ustep*(i+.5)
            zz=z+.18+hstep*(j+.5)
            ow=ustep*.70;oh=hstep*.81
            shape=octagon(u,zz,ow,oh,.24)
            ring(f,shape,.061,-.36,-.226,'raised bronze','raised grille octagons')
            theta=np.linspace(0,math.tau,19 if lod else 33)
            path=[f.point(u+ow*.31*math.cos(t),zz+oh*.30*math.sin(t),-.277)for t in theta]
            f.builder.tube(path,.039,'bronze iron',5 if lod else 8,f.label+'/grille loops')
            for sx in [-1,1]:
                for sz in [-1,1]:
                    f.line((u+sx*ow*.23,zz+sz*oh*.32,-.29),(u+sx*ustep*.45,zz+sz*hstep*.40,-.29),
                           .031,'bronze iron',5 if lod else 7,'iron diagonal ties')
    for edge in [-1,1]:
        u=x+edge*(w/2-.23)
        f.line((u,z+.15,-.27),(u,z+h-.15,-.27),.044,'bronze iron',6,'flanking grille rods')


def bank_sign(f):
    # A dated, removable public-facing sign. The historic institution name is documented separately.
    f.box(0,8.63,10.81,1.84,.28,.10,'blue enamel','2015 blue sign')
    f.box(.8,8.68,9.15,1.60,.10,.249,'white enamel','white sign field')
    f.prism(Polygon([(-2.13,9.21),(-2.78,9.21),(-3.22,8.80),(-3.22,8.47),
                    (-2.8,8.11),(-2.34,8.11),(-1.96,8.50),(-2.21,8.73),
                    (-2.54,8.43),(-2.80,8.66),(-2.48,8.99),(-2.19,8.99)]),
            .304,.350,'blue enamel','construction bank sign emblem')
    add_facade_lettering(f,'中国建设银行',.99,8.89,5.77,.53,.304,.35,'sign letters',font=FONT,label='Chinese name')
    add_facade_lettering(f,'China Construction Bank',.96,8.40,5.72,.265,.302,.338,'sign letters',font=FONT,label='English name')


def cornice(b,f,lod):
    for x in np.linspace(-11.48,11.48,13):
        wing=Facade(b,[x-.25,.40],[x+.25,.40],'Soffit')
        poly=Polygon([(-.20,22.94),(.20,22.94),(.23,23.49),(-.23,23.49)])
        wing.prism(poly,-1.36,.245,'carved granite','projecting stone bracket')
        wing.box(0,23.06,.28,.18,1.67,-.51,'recessed stone','corbel lower rebate')
    for z,h,depth,d,mat in [(22.91,.16,1.76,-.36,'granite ashlar'),(23.42,.20,2.23,-.12,'recessed stone'),
                           (23.58,.17,2.39,-.08,'carved granite'),(23.82,.30,2.29,-.07,'granite ashlar'),
                           (24.04,.15,2.36,-.07,'roof coping')]:
        # The caps project toward the street yet remain inside the documented frontage.
        b.box((0,1.29+d,z),(24.12,depth,h),mat,label='Cornice/continuous horizontal courses')


def assemble(b,lod):
    f=Facade(b,[-HALF,.49],[HALF,.49],'Bank front')
    entrance=opening(0,.19,4.19,7.63)
    iron=[opening(x,.79,2.54,6.88)for x in [-8.20,8.20]]
    f.wall(.08,9.34,[entrance,*iron],.52,'granite ashlar')
    ashlar(f,box(-HALF,.08,HALF,9.34),[entrance,*iron])
    for x in [-5.00,5.00]:
        plaque=opening(x,1.14,2.62,6.39)
        ring(f,plaque,.115,.018,.087,'recessed stone','rectangular field frame')
        ring(f,plaque.buffer(.11,join_style='mitre'),.042,.018,.074,'carved granite','rectangular stone bead')
    for x in [-8.20,8.20]:
        grille(f,x,.79,2.54,6.88,True,lod)
    central_doors(f,lod)
    grille(f,0,5.72,4.12,2.05,False,lod)
    bank_sign(f)
    for z,h in [(.27,.22),(.68,.15),(8.97,.13),(9.18,.17)]:
        base=box(-HALF,z-h/2,HALF,z+h/2).difference(unary_union([entrance,*iron]))
        f.prism(base,.012,.126,'plinth stone' if z<1 else 'carved granite','base and bank lintel courses')
    back=Facade(b,[-HALF,2.54],[HALF,2.54],'Upper screen')
    holes=[opening(x,z,1.04,1.64)for x in WINDOW_X for z in WINDOW_Z]
    back.wall(9.14,22.89,holes,.36,'granite ashlar')
    ashlar(back,box(-HALF,9.14,HALF,22.89),holes)
    for x in WINDOW_X:
        for z in WINDOW_Z: glass(back,x,z)
    for x in COLUMN_X: chamfered_column(b,x)
    cornice(b,f,lod)
    plan=box(-HALF,.08,HALF,BACK)
    b.plan_prism(plan,0.,.082,'plinth stone','Section/base')
    b.plan_prism(box(-HALF,.36,HALF,BACK),9.12,9.28,'plinth stone','Section/colonnade ledge')
    b.plan_prism(box(-HALF,.14,HALF,BACK),23.99,24.13,'roof coping','Section/roof')
    b.box((0,BACK-.09,12.00),(2*HALF,.18,23.96),'recessed stone',label='Section/rear closure')
    for x in [-HALF+.07,HALF-.07]:
        b.box((x,2.52,12.0),(.14,3.99,23.97),'granite ashlar',label='Section/lateral return')


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
