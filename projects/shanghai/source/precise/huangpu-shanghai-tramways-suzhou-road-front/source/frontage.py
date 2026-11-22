"""Street wall, four pilaster shafts, window joinery, rusticated base and balcony on the 2015 Shanghai Tramways façade."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from photo_plane import HALF_WIDTH, position
from material_names import MATERIAL

ROOT = Path(__file__).resolve().parents[1] / 'measurements'
CREAM = 'Cream projecting stucco'
SHADOW = 'Ochre undercut moulding'
SEAM = 'Weathered masonry joints'
RED = 'Russet window cornices'
KEY = 'Highlighted red keys'
TIMBER = 'Painted maroon window stiles'
GLASS = 'Blue-grey glazing'
DARK = 'Deep recessed glazing'
IRON = 'Black balcony iron'
DOOR = 'Interior door panels'
def pigment(rgb,roughness=.84,metallic=0.):
    a=np.asarray(rgb)/255
    return dict(color=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)
PALETTE={CREAM:pigment([204,193,161]),SHADOW:pigment([161,150,126]),SEAM:pigment([145,137,112]),
         RED:pigment([146,87,70]),KEY:pigment([164,104,83]),TIMBER:pigment([102,65,56]),
         GLASS:pigment([105,127,129],.38,.06),DARK:pigment([60,71,72],.42,.05),
         IRON:pigment([49,48,44],.68,.23),DOOR:pigment([93,61,53])}

def block(b,label,x0,x1,y0,y1,z0,z1,mat):
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],mat,label=label)

def course(b,f,z,h,projection,material,label,ext=.0):
    f.prism(box(-HALF_WIDTH-ext,z,HALF_WIDTH+ext,z+h),-.02,projection,material,label)
    block(b,label+' photo-right return',HALF_WIDTH-.012,HALF_WIDTH+projection,.04,1.48,z,z+h,material)

def glazing(f,shape,tier,column):
    name=f'{tier} bay {column}'
    x0,z0,x1,z1=shape.bounds;w=x1-x0;h=z1-z0
    # Behind the continuous reveal, glazing laps under the fixed frame.
    f.prism(shape.buffer(.015,join_style=2),-.305,-.292, DARK if tier=='street' else GLASS,name+' glass')
    inner=shape.buffer(-(.055 if w>.70 else .044),join_style=2)
    transom=z0+h*(.67 if tier!='attic' else .56)
    bars=[box(x0,transom-.025,x1,transom+.025)]
    if w>1.04 and tier not in ('street','attic'):
        centre=(x0+x1)/2
        bars.append(box(centre-.018,z0,centre+.018,z1))
    if tier=='street':
        zrail=z0+h*.73
        bars.append(box(x0,zrail-.017,x1,zrail+.017))
    frame=shape.buffer(.006,join_style=2).difference(inner.difference(unary_union(bars)))
    f.prism(frame,-.291,-.230,TIMBER,name+' sash and transom')
    if tier=='street':
        for j in range(1,6):
            u=x0+w*j/6
            f.prism(box(u-.012,z0,u+.012,z1).intersection(shape),-.133,-.104,IRON,name+' guard bars')
        for j in (1,2):
            z=z0+h*j/3
            f.prism(box(x0,z-.015,x1,z+.015),-.13,-.102,IRON,name+' guard rails')

def window_trim(f,shape,tier,column):
    x0,z0,x1,z1=shape.bounds
    width=x1-x0;name=f'{tier} bay {column}'
    if tier=='attic':return
    if tier!='street':
        for number,(h0,h1,side,depth) in enumerate(((-.21,-.12,.042,.083),(-.125,-.065,.084,.134),(-.067,.003,.136,.194))):
            f.prism(box(x0-side,z0+h0,x1+side,z0+h1),.002,depth,RED,name+f' sill ledge {number+1}')
    if tier=='upper':return
    # Five stones fan outward from the head. Their thin joint is the dark
    # interstice between adjacent voussoirs and continues around the returns.
    fan=.20 if tier=='street' else .245
    top=z1+(.495 if tier=='street' else .51)
    for j in range(5):
        aa=j/5; bb=(j+1)/5
        low=lambda v:x0+v*width
        hi=lambda v:x0-fan+v*(width+2*fan)
        raised=.095 if j==2 else .0
        outline=Polygon([(low(aa)+.004,z1-.003),(low(bb)-.004,z1-.003),
                         (hi(bb)-.007,top+raised),(hi(aa)+.007,top+raised)])
        depth=.135 if j==2 else .097
        f.prism(outline,-.004,depth,KEY if j==2 else RED,name+f' splayed lintel {j+1}')

def rusticated_base(b,f,door,apertures):
    mask=unary_union([door,*apertures]);z0=.0
    ends=[.49,1.04,1.55,2.02,2.50,2.98,3.45,3.93,4.40,4.88,5.17]
    for j,z1 in enumerate(ends):
        panel=box(-HALF_WIDTH,z0+.014,HALF_WIDTH,z1-.014).difference(mask)
        f.prism(panel,-.005,.038 if j else .11,MATERIAL,f'rusticated course {j+1}')
        block(b,f'ground photo-right course {j+1}',HALF_WIDTH-.015,HALF_WIDTH+.035,.04,1.47,z0+.014,z1-.014,MATERIAL)
        z0=z1

def entrance_aperture():
    d=json.loads((ROOT/'entrance.json').read_text())
    xz=lambda pts:[position(*uv,d['front_arch_face_y_m'])[[0,2]].tolist() for uv in pts]
    arc=xz(d['arch_outer'])
    return Polygon([*arc,[arc[-1][0],0],[arc[0][0],0]])

def entrance_back(b,f,door):
    x0,_,x1,z1=door.bounds
    # The entrance wall ends before its inset leaves. Continue the cut edge
    # back to the door, closing both jambs and the arch soffit.
    reveal = door.buffer(.18, join_style=2).difference(door)
    f.prism(reveal,-.751,-.388,SHADOW,'masonry return between street wall and timber door')
    f.prism(door.buffer(.03),-.75,-.723,DOOR,'entrance recessed timber backing')
    for j in range(2):
        xx=x0+(x1-x0)*j/2
        panel=box(xx+.07,.36,xx+(x1-x0)/2-.07,2.35).intersection(door)
        f.prism(panel,-.72,-.70,DARK,f'entrance dark glazed door {j+1}')
    f.prism(box(x0,.0,x1,.11),-.74,.06,SHADOW,'entrance threshold')

def pilasters(b,f):
    wreaths=json.loads((ROOT/'four-photographed-wreaths.json').read_text())['wreaths']
    for i,r in enumerate(wreaths):
        pts=np.asarray([position(*p,-.21) for p in r['outer']]);cx=(pts[:,0].min()+pts[:,0].max())/2
        w=1.205 if i in (1,2) else 1.06;left=cx-w/2;right=cx+w/2;name=f'pilaster {i+1}'
        block(b,name+' shaft',left,right,-.21,.024,5.29,16.72,CREAM)
        def border(bottom,top,inset):
            outer=box(left+.105,bottom,right-.105,top)
            inner=box(left+.105+inset,bottom+inset,right-.105-inset,top-inset)
            f.prism(outer.difference(inner),.208,.238,SHADOW,name+' incised panel fillet')
        border(5.79,16.57,.021)
        for j in range(14):
            z=5.64+j*.774
            # Fine apparent bed joints at the outer borders, broken by the panel.
            for a,c in [(left,left+.091),(right-.091,right)]:
                f.prism(box(a,z,c,z+.009),.208,.215,SEAM,name+' edge joints')
        block(b,name+' capital neck',left-.045,right+.045,-.271,-.12,16.68,16.85,SHADOW)
        block(b,name+' capital slab',left-.126,right+.126,-.37,-.13,16.85,17.00,CREAM)
        for j in range(8):
            x=left+.036+j*(w-.072)/7
            block(b,name+' capital dentils',x-.033,x+.033,-.36,-.238,16.73,16.847,CREAM)
        block(b,name+' attic pier',left+.034,right-.034,-.19,.02,17.77,21.12,CREAM)
        f.prism(box(left+.19,18.02,right-.19,20.65).difference(box(left+.22,18.05,right-.22,20.62)),.188,.205,SHADOW,name+' attic panel')
        block(b,name+' attic cap',left-.02,right+.02,-.238,-.08,20.99,21.10,CREAM)
        # Square red brackets at the ground-level string course.
        if i in (1,2):
            continue  # The portico's two inner consoles follow the measured door surround.
        q=.30
        f.prism(Polygon([(cx-q,5.12),(cx+q,5.12),(cx+q*.77,4.43),(cx,4.34),(cx-q*.77,4.43)]),0,.19,RED,name+' lower red console')
        for side in (-1,1):
            x=cx+side*(q-.03)
            f.prism(box(x-.035,4.46,x+.035,5.075),.19,.24,KEY,name+' console edge')

def add_frontage(b,lod):
    f=Facade(b,(-HALF_WIDTH,0),(HALF_WIDTH,0),'Street')
    records=json.loads((ROOT/'facade-apertures.json').read_text())['openings']
    apertures=[Polygon(r['rectified_xz_m']) for r in records]
    door=entrance_aperture()
    f.wall(.0,21.21,[*apertures,door],.39,MATERIAL)
    block(b,'Visible photo-right corner return',HALF_WIDTH-.137,HALF_WIDTH,.385,1.48,.013,21.21,MATERIAL)
    rusticated_base(b,f,door,[s for s,r in zip(apertures,records) if r['tier']=='street'])
    for shape,row in zip(apertures,records):
        glazing(f,shape,row['tier'],row['column'])
        window_trim(f,shape,row['tier'],row['column'])
    entrance_back(b,f,door);pilasters(b,f)
    for label,levels in [('first string',[(5.10,.07,.13),(5.17,.083,.204),(5.253,.112,.30),(5.365,.063,.37)]),
                          ('upper cornice',[(16.98,.08,.16),(17.06,.12,.257),(17.18,.075,.34),(17.255,.142,.47),(17.397,.095,.56),(17.492,.105,.61),(17.597,.145,.67)]),
                          ('roof cornice',[(20.99,.084,.13),(21.074,.105,.22),(21.179,.096,.309),(21.275,.082,.407),(21.357,.092,.49)])]:
        for j,(z,h,depth) in enumerate(levels):course(b,f,z,h,depth,RED if label=='roof cornice' and j==4 else CREAM if j%3 else SHADOW,label+f' {j+1}',depth*.66)
    for j,x in enumerate(np.arange(-HALF_WIDTH+.08,HALF_WIDTH,.178)):
        block(b,'Continuous cornice dentils',x,x+.098,-.32,-.16,16.92,17.068,CREAM)
    ground_sill=box(-HALF_WIDTH,.85,HALF_WIDTH,.927).difference(door.buffer(.04))
    f.prism(ground_sill,-.02,.117,CREAM,'ground window sill interrupted at doorway')
