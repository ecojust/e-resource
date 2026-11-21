"""The projecting garden entrance of the 1932 China Welfare Institute house."""
from math import cos, pi, sin, sqrt
from shapely.geometry import LineString, Polygon, box
from photo_architecture import Facade

PALETTE = {name: {'color': rgb, 'roughness': rough} for name,rgb,rough in [
    ('grey porch render', [.44,.44,.40], .96), ('pale stone trim',[.65,.64,.59],.92),
    ('soffit plaster',[.56,.55,.49],.91), ('paving joint',[.23,.22,.19],.92),
    ('paving slab',[.37,.36,.32],.90), ('lion limestone',[.48,.46,.40],.90),
    ('carved recess',[.33,.31,.27],.94), ('stained oak',[.16,.08,.04],.65),
    ('recessed oak',[.12,.058,.032],.72), ('door glass',[.077,.107,.093],.25),
    ('glazing grille',[.042,.051,.045],.63), ('bronze fitting',[.18,.14,.075],.64),
    ('translucent lamp',[.63,.57,.41],.44) ]}
WIDTH, DEPTH, CEILING = 5.56, 3.06, 4.18
CLEAR, SPRING, RISE = 3.88, 3.31, .49

def top(x,width,spring,rise):
    radius=width*width/(8*rise)+rise/2
    return spring+rise-radius+sqrt(max(0,radius*radius-x*x))

def arch(width,spring,rise,n,base=-.025):
    xs=[width*(.5-i/n) for i in range(n+1)]
    return Polygon([(-width/2,base),(width/2,base),*((x,top(x,width,spring,rise)) for x in xs)])

def porch_front(b,lod):
    face=Facade(b,(-WIDTH/2,0),(WIDTH/2,0),'garden front')
    n=20 if lod else 44
    a=arch(CLEAR,SPRING,RISE,n)
    rings=[a,arch(CLEAR+.07,SPRING+.066,RISE,n),
           arch(CLEAR+.17,SPRING+.133,RISE+.014,n),arch(CLEAR+.56,SPRING+.19,RISE+.035,n)]
    face.prism(box(-WIDTH/2,0,WIDTH/2,CEILING+.14).difference(rings[-1]),-.47,0,
               'grey porch render','outer piers and spandrel')
    for i,(inner,outer,d) in enumerate(zip(rings,rings[1:],(.035,.073,.105))):
        face.prism(outer.difference(inner),-.47,d,'pale stone trim',f'stepped arch profile {i+1}')
    for side in (-1,1):
        face.box(side*(WIDTH+CLEAR)/4,.125,(WIDTH-CLEAR)/2+.08,.25,.59,-.20,
                 'pale stone trim','pier base')
    face.box(0,CEILING+.14,WIDTH+.10,.12,.61,-.18,'pale stone trim','balcony slab edge')
    for side in (-1,1):
        x=side*WIDTH/2
        a,z=((x,0),(x,DEPTH)) if side>0 else ((x,DEPTH),(x,0))
        sideface=Facade(b,a,z,'east return' if side>0 else 'west return')
        small=arch(2.12,3.14,.49,n);large=arch(2.28,3.23,.50,n)
        sideface.prism(box(-DEPTH/2,0,DEPTH/2,CEILING+.07).difference(large),
                       -.40,0,'grey porch render','piers of lateral opening')
        sideface.prism(large.difference(small),-.40,.047,'pale stone trim','lateral arch rim')

def recessed_door(b,lod):
    face=Facade(b,(-WIDTH/2,DEPTH),(WIDTH/2,DEPTH),'timber entrance')
    n=20 if lod else 40
    aperture=arch(3.62,2.88,.39,n,.16);outer=arch(3.90,3.00,.41,n,.14);glass=arch(3.46,2.82,.37,n,.20)
    face.prism(box(-WIDTH/2,0,WIDTH/2,CEILING).difference(outer),-.23,.02,'soffit plaster','entrance wall')
    face.prism(outer.difference(aperture),-.11,.09,'pale stone trim','surround')
    face.prism(aperture.difference(glass),-.04,.045,'stained oak','arched door jambs')
    face.prism(glass,-.14,-.07,'door glass','leaf and transom glazing')
    for i in range(5):
        x=(i-2)*.865;head=top(x,3.46,2.82,.37)
        face.box(x,(.16+head)/2,.076 if i!=2 else .095,head-.16,.085,-.023,'stained oak','stiles')
    face.box(0,2.47,3.51,.10,.089,-.014,'stained oak','transom rail')
    for i in range(4):
        x=(i-1.5)*.865
        face.box(x,.815,.79,1.24,.079,-.032,'stained oak','panel framing')
        face.box(x,.814,.683,1.03,.025,.009,'recessed oak','lower leaf field')
        face.box(x,1.44,.80,.065,.085,-.027,'stained oak','bottom glazing rail')
        if i in (1,2):
            face.box(x+(.312 if i==1 else -.312),1.26,.032,.232,.085,.049,'bronze fitting','door pull')
        for z0,z1 in ((1.53,2.32),(2.56,2.86)):
            outline=box(x-.292,z0,x+.292,z1)
            grille=outline.boundary.buffer(.009,join_style=2)
            if not lod:
                for side in (-1,1):
                    u=x+side*.292
                    for z,direction in ((z0+.066,1),(z1-.066,-1)):
                        pts=[(u,z),(u-side*.083,z),(u-side*.083,z+.044*direction),(u-side*.133,z+.044*direction)]
                        grille=grille.union(LineString(pts).buffer(.009,join_style=2))
                mid=(z0+z1)/2
                motif=[(x,mid+.065),(x+.057,mid),(x,mid-.065),(x-.057,mid),(x,mid+.065)]
                grille=grille.union(LineString(motif).buffer(.010,join_style=2))
            face.prism(grille,-.018,.003,'glazing grille','stepped geometric ironwork')
    for y,z,length in ((DEPTH-.14,.072,.38),(DEPTH-.38,.030,.29)):
        b.box((0,y,z),(3.91,length,z*2),'pale stone trim',label='stone sill steps')

def body(b,sections,n,mat,label):
    # Longitudinal sections run from the garden-facing nose to the tail.
    vertices=[(x+rx*cos(2*pi*i/n),y,z+rz*sin(2*pi*i/n))
              for x,y,z,rx,rz in sections for i in range(n)]
    faces=[tuple(range(n)),tuple(range(len(vertices)-1,len(vertices)-n-1,-1))]
    for j in range(len(sections)-1):
        for i in range(n):
            a=j*n+i;c=j*n+(i+1)%n;faces.append((a,a+n,c+n,c))
    b.add(vertices,faces,mat,label)

def lion(b,x,lod):
    y=DEPTH-1.11
    for z,h,w,length in ((.05,.10,.65,1.13),(.255,.31,.53,1.015),(.459,.101,.68,1.17)):
        b.box((x,y+.37,z),(w,length,h),'lion limestone',label='lion pedestal courses')
    n=10 if lod else 18
    def sculpt(sections,label,mat='lion limestone'):
        cells=[(x+u,y+v,z+.513,rx,rz) for u,v,z,rx,rz in sections]
        body(b,cells,n,mat,label)
    sculpt([(0,.08,.29,.141,.20),(0,.19,.33,.221,.294),(0,.36,.29,.218,.238),
            (0,.65,.225,.183,.167),(0,.78,.194,.202,.164),(0,.88,.14,.128,.12)],'recumbent lion body')
    sculpt([(0,-.267,.447,.07,.042),(0,-.225,.450,.121,.070),(0,-.12,.49,.143,.104),
            (0,.024,.522,.182,.19),(0,.124,.49,.206,.232),(0,.22,.439,.163,.205)],'muzzle and carved mane')
    sculpt([(0,-.235,.365,.080,.016),(0,-.172,.366,.101,.032),(0,-.098,.367,.132,.053),
            (0,.02,.385,.142,.111)],'lower jaw')
    sculpt([(0,-.283,.474,.067,.018),(0,-.256,.485,.083,.026),(0,-.223,.491,.078,.017)],
           'broad nose','carved recess')
    for side in (-1,1):
        sculpt([(side*.123,-.155,.075,.084,.040),(side*.125,-.086,.084,.091,.056),
                (side*.136,.028,.156,.076,.126),(side*.147,.15,.245,.096,.222)],'forepaw and leg')
        sculpt([(side*.123,.49,.072,.069,.039),(side*.15,.55,.078,.086,.049),
                (side*.153,.67,.14,.081,.11),(side*.128,.755,.188,.092,.119)],'folded hind paw')
        sculpt([(side*.14,.022,.646,.028,.026),(side*.169,.084,.652,.036,.043),
                (side*.146,.134,.623,.041,.022)],'rounded lion ear')
        if not lod:
            for j in range(5):
                v=.006+j*.037
                pts=[(x+side*.156,y+v,.513+.635-j*.012),(x+side*.192,y+v+.027,.513+.538-j*.018),
                     (x+side*.200,y+v+.060,.513+.444-j*.024),(x+side*.177,y+v+.084,.513+.372-j*.019)]
                b.tube(pts,.020,'lion limestone',7,'cut mane ridges')
            sculpt([(side*.123,-.126,.544,.018,.011),(side*.136,-.105,.554,.021,.017),
                    (side*.135,-.081,.557,.011,.012)],'eye socket','carved recess')


def lighting(b,lod):
    # The angled 2023 photograph resolves faceted pale posts with bronze caps.
    # Both posts terminate below the balcony slab. A small pendant hangs
    # within the open bay in the frontal photograph.
    for side in (-1,1):
        x,y=side*2.40,-.205
        b.lathe((x,y),[(.004,.345),(.105,.345),(.13,.314),(.32,.31),
                      (.355,.277),(3.19,.265),(3.25,.296),(3.34,.300)],
                'pale stone trim',6,'six-sided lamp post')
        b.lathe((x,y),[(3.34,.264),(3.385,.279)],'bronze fitting',6,'lantern foot')
        b.lathe((x,y),[(3.385,.239),(3.713,.224)],'translucent lamp',6,'hexagonal lantern panes')
        b.lathe((x,y),[(3.709,.244),(3.742,.28),(3.79,.24),(3.827,.055)],
                'bronze fitting',6,'shallow lantern cap')
        for j in range(6):
            angle=2*pi*j/6
            b.tube([(x+.24*cos(angle),y+.24*sin(angle),3.38),
                    (x+.227*cos(angle),y+.227*sin(angle),3.72)],
                   .013,'bronze fitting',5,'lantern glazing bars')
    y=DEPTH*.49
    b.lathe((0,y),[(3.82,.018),(4.11,.018)],'bronze fitting',8,'pendant stem')
    b.lathe((0,y),[(3.67,.073),(3.70,.136),(3.80,.127)],'translucent lamp',8,'pendant glass')
    b.lathe((0,y),[(3.797,.141),(3.825,.148),(3.875,.039)],'bronze fitting',8,'pendant cap')

def add_building(b,lod=False):
    porch_front(b,lod)
    recessed_door(b,lod)
    lighting(b,lod)
    b.box((0,DEPTH/2,-.071),(WIDTH,DEPTH,.142),'paving joint',label='porch paving subbase')
    count=3 if lod else 6
    for i in range(count):
        for j in range(3):
            width,depth=WIDTH/count,DEPTH/3
            b.box(((i+.5)*width-WIDTH/2,(j+.5)*depth,-.012),(width-.014,depth-.014,.026),
                  'paving slab',label='individual paving slabs')
    b.box((0,DEPTH/2,CEILING+.015),(WIDTH,DEPTH,.205),'soffit plaster',label='ceiling of projecting porch')
    for side in (-1,1):lion(b,side*2.03,lod)
