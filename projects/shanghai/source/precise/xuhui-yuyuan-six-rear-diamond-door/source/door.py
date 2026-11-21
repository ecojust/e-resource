"""Surveyed timber door and forged iron at the back entrance of no. 6, Lane 1350."""
from math import cos, pi, sin
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade

PALETTE={
    'painted teak':{'color':[.30,.114,.078], 'roughness':.76},
    'alternate teak':{'color':[.323,.126,.088], 'roughness':.77},
    'rebated seam':{'color':[.145,.061,.039], 'roughness':.87},
    'timber frame':{'color':[.209,.083,.056], 'roughness':.70},
    'hammered iron':{'color':[.202,.116,.079], 'roughness':.73, 'metallic':.36},
    'textured glass':{'color':[.70,.686,.56], 'roughness':.68, 'alpha':.82},
    'dark patinated brass':{'color':[.171,.180,.149], 'roughness':.53,'metallic':.65},
    'engraved brass':{'color':[.73,.64,.43], 'roughness':.5,'metallic':.46},
    'cream plaster':{'color':[.78,.731,.621], 'roughness':.94},
    'mortar':{'color':[.61,.579,.505], 'roughness':.95},
    'brown brick':{'color':[.57,.37,.29], 'roughness':.93},
    'salmon brick':{'color':[.63,.424,.345], 'roughness':.93},
    'stone sill':{'color':[.53,.513,.466], 'roughness':.93},
}
# D1 on the building department's original door schedule is 3 ft 3 in by 7 ft 6 in.
W=0.9906
H=2.286
SILL=.176
CX=-.008
CZ=SILL+1.527
R=.232

def strip(points,width):
    return LineString(points).buffer(width/2,cap_style='flat',join_style='round',quad_segs=3)

def close_photo(x,y):
    # 493 by 740 display of picture 7, with the internal diamond at (249,359).
    return (CX+(x-249)*R/125, CZ+(359-y)*R/130)

def bezier(points,steps):
    a,b,c,d=points
    return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in range(2))for t in (i/steps for i in range(steps+1))]

def install_grille(face,lod,opening):
    # The broad low arch, the smaller lower arc and the coiled upper stem are
    # separately visible in picture 7. The right end of the aperture is behind
    # a notice. Each line stops at the photographed frame.
    paths={
        'inner lower arch':((212,457),(230,415),(267,414),(285,456)),
        'outer lower arch':((186,425),(210,372),(280,374),(314,422)),
        'diagonal stem from left':((158,371),(179,345),(209,323),(239,301)),
        'diagonal stem from right':((208,392),(245,361),(303,326),(331,302)),
        'left diamond crossing':((143,308),(170,333),(196,363),(217,386)),
        'right diamond crossing':((265,309),(292,335),(322,363),(341,390)),
        'upper outer curl':((211,335),(258,306),(284,275),(250,265)),
        'upper inner curl':((250,265),(212,246),(202,301),(237,310)),
        'curl return':((237,310),(262,315),(275,281),(254,281)),
        'curl terminal':((254,281),(247,280),(245,290),(252,290)),
    }
    for label,control in paths.items():
        poly=strip([close_photo(*p)for p in bezier(control,8 if lod else 20)],.009 if 'curl' in label else .008)
        poly=poly.intersection(opening)
        if poly.area>.000008:face.prism(poly,.019,.031,'hammered iron',label)
    # Solid timber is removed through the full thickness of the glazed aperture.
    face.prism(opening.buffer(-.004),-.008,-.002,'textured glass','recessed glazing')
    face.prism(opening.buffer(.010,join_style='mitre').difference(opening.buffer(-.004,join_style='mitre')),.012,.028,'timber frame','sloped glazing bead')

def add_building(builder,lod=False):
    f=Facade(builder,(-.5,0),(.5,0),'No 6 rear door')
    opening=Polygon([(CX,CZ+R),(CX+R,CZ),(CX,CZ-R),(CX-R,CZ)])
    leaf=box(-W/2,SILL,W/2,SILL+H)
    f.prism(leaf.difference(opening),-.041,.002,'rebated seam','complete cut timber leaf')
    # Parallel V-jointed boards run diagonally to form the observed large squares;
    # their original lower rail is horizontal, as shown on the D1 working drawing.
    lower=SILL+.29
    for i in range(-7,8):
        for j in range(-6,12):
            pitch=.488;ax=i*pitch+(.244 if j%2 else 0)+CX;az=lower+j*pitch/2
            quad=Polygon([(ax,az+pitch/2),(ax+pitch/2,az),(ax,az-pitch/2),(ax-pitch/2,az)])
            cell=quad.buffer(-.0015,join_style='mitre').intersection(leaf).intersection(box(-.6,lower+.003,.6,SILL+H)).difference(opening)
            if cell.area>.00012:f.prism(cell,.002,.012,'alternate teak' if (i+j)%5==1 else 'painted teak',f'diagonal teak {i+7:02} {j+6:02}')
    f.prism(box(-W/2,SILL,W/2,lower-.002),.002,.012,'painted teak','horizontal bottom rail')
    install_grille(f,lod,opening)
    for h,ext,depth in [(0,.052,.052),(1,.075,.038),(2,.091,.024)]:
        # U-shaped jambs and head, no invented fourth casing across the sill.
        prev=[.002,.051,.074][h];outer=box(-W/2-ext,SILL,W/2+ext,SILL+H+ext)
        inner=box(-W/2-prev,SILL-.02,W/2+prev,SILL+H+prev)
        f.prism(outer.difference(inner),-.031,depth,'timber frame','frame step '+str(h))
    edge=.872; inside=W/2+.091; top=SILL+H+.092
    for side in (-1,1):
        l,r=sorted([side*inside,side*edge]);f.prism(box(l,SILL,r,top),-.12,-.025,'cream plaster','recess back wall '+str(side))
        f.prism(box(l,SILL,r,.659),-.025,.006,'mortar','brick joints '+str(side))
        for row in range(6):
            for col in range(4):
                x=l+(col-(row%2)*.5)*.205
                a,b=max(l,x+.005),min(r,x+.199)
                if b>a+.002:f.prism(box(a,SILL+row*.079+.004,b,SILL+row*.079+.074),.006,.016,('salmon brick','brown brick')[(row+col)%2],f'brick {side} {row} {col}')
        # The full photo shows the plaster return and its brick skirting going towards the photographer.
        l,r=sorted([side*edge,side*(edge+.074)])
        f.box((l+r)/2,(top+SILL)/2,r-l,top-SILL,.48,.17,'cream plaster','side return '+str(side))
        f.box((l+r)/2,(SILL+.659)/2,r-l+.009,.659-SILL,.48,.17,'brown brick','return plinth '+str(side))
    f.box(0,top+.115,2*edge,.23,.49,.166,'cream plaster','recessed lintel and soffit')
    f.box(0,SILL*.5,2*edge,SILL,.51,.158,'stone sill','entry threshold')
    # Black brass number plate, folded edge and original raised numeral 6.
    px,pz=.206,SILL+1.977
    f.box(px,pz,.141,.091,.008,.019,'dark patinated brass','number plate')
    numeral=[(.523,.82),(.414,.67),(.371,.54),(.372,.41),(.418,.35),(.484,.35),(.534,.40),(.536,.48),(.504,.53),(.436,.54),(.382,.49)]
    f.prism(strip([(px+(x-.45)*.14,pz+(y-.50)*.10)for x,y in numeral],.0025),.022,.026,'engraved brass','raised numeral six')
    # The lower address is legible in the published close view. Individual
    # strokes are drawn here, with no external characters or photo texture.
    if not lod:
        letters={
            '一':[[ (.08,.50),(.92,.50)]],
            '三':[[ (.17,.82),(.82,.82)],[(.23,.54),(.78,.54)],[(.07,.20),(.92,.20)]],
            '五':[[ (.10,.85),(.89,.85)],[(.46,.82),(.30,.21)],[(.21,.58),(.75,.58),(.72,.22)],[(.06,.18),(.95,.18)]],
            '〇':[[(.50+.31*cos(k*2*pi/20),.50+.38*sin(k*2*pi/20)) for k in range(21)]],
            '弄':[[ (.15,.86),(.84,.86)],[(.52,.85),(.52,.50)],[(.22,.70),(.78,.70)],[(.09,.49),(.89,.49)],[(.08,.34),(.93,.34)],[(.35,.44),(.34,.23),(.16,.06)],[(.69,.44),(.69,.08)]],
            '后':[[ (.81,.89),(.20,.81),(.20,.55),(.16,.24),(.05,.07)],[(.20,.63),(.90,.63)],[(.36,.45),(.36,.12),(.82,.12),(.82,.45),(.36,.45)]],
            '门':[[ (.26,.92),(.39,.79)],[(.14,.73),(.14,.11)],[(.43,.82),(.85,.82),(.85,.11),(.71,.16)]]
        }
        for ix,letter in enumerate('一三五〇弄后门'):
            paths=letters[letter]; left=px-.055+ix*.016
            outlines=[strip([(left+.014*x,pz-.032+.014*z) for x,z in line],.00095) for line in paths]
            f.prism(unary_union(outlines),.023,.0245,'engraved brass',f'address inscription {ix+1}')
        for sx in (-1,1):
            for sz in (-1,1):f.prism(Point(px+sx*.060,pz+sz*.036).buffer(.0024,quad_segs=4),.023,.027,'engraved brass',f'plate rivet {sx} {sz}')
    f.prism(Point(.443,SILL+1.289).buffer(.018,quad_segs=6 if lod else 13),.016,.029,'dark patinated brass','round escutcheon')
    grip=strip([(.443,SILL+1.218),(.433,SILL+1.20),(.433,SILL+1.134),(.442,SILL+1.118)],.011)
    f.prism(grip,.019,.050,'dark patinated brass','upright door pull')
