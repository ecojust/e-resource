"""The two measured curved bars, their posts, and the adjacent wall returns at Wusheng Road."""
import json
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import LineString, Polygon
from photo_architecture import Facade
from material_names import MATERIAL
from photo_plane import position

MEASUREMENTS = Path(__file__).resolve().parents[1] / 'measurements'
IRON = 'Painted iron entrance frame'
CAP = 'Black metal fixings'
MORTAR = 'Buff brick mortar'
TILE = 'Pale ceramic facing tile'
JOINT = 'Weathered grey tile grout'
ENAMEL = 'Green enamel address field'
WHITE = 'Ivory address lettering'
def pigment(rgb, rough=.78, metal=0.):
    a = np.asarray(rgb)/255.
    return dict(color=np.where(a < .04045, a/12.92, ((a+.055)/1.055)**2.4).tolist(), roughness=rough, metallic=metal)
PALETTE = {IRON:pigment([49,52,50],.62,.36), CAP:pigment([43,45,43],.64,.39),
           MORTAR:pigment([143,115,99]), TILE:pigment([192,194,187],.52),
           JOINT:pigment([126,128,121]), ENAMEL:pigment([43,99,72],.5,.12), WHITE:pigment([217,217,194],.64)}

def box(b,label,x0,x1,y0,y1,z0,z1,mat):
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2], [x1-x0,y1-y0,z1-z0], mat, label=label)

def bow(b, outline, name, lod):
    x,z=np.transpose([position(*uv,.035)[[0,2]] for uv in outline])
    xs=np.linspace(x[0],x[-1],28 if lod else 71)
    zs=PchipInterpolator(x,z)(xs)
    section=LineString(list(zip(xs,zs))).buffer(.0145 if name=='lower' else .02,
                 cap_style='flat', join_style='round',quad_segs=2)
    f=Facade(b,(-4,0),(4,0),'Curved head frame')
    f.prism(section,-.061,-.009,IRON,name+' measured curved bar')
    return x,z

def post(b,x,z,index):
    name=['Left gatepost','Right gatepost'][index]
    box(b,name+' shaft',x-.035,x+.035,-.017,.068,.014,z+.019,IRON)
    box(b,name+' foot sleeve',x-.046,x+.046,-.028,.08,.012,.128,CAP)
    box(b,name+' crown closure',x-.041,x+.041,-.023,.075,z+.012,z+.035,CAP)
    for idx,h in enumerate((.19,1.90)):
        b.lathe((x + (.055 if index==0 else -.056),.023),[(h,.015),(h+.018,.021),(h+.102,.021),(h+.119,.015)],
                CAP,segments=12,label=name+' hinge barrel '+str(idx+1))

def side_fence(b,lod):
    # In the 2020 oblique survey the tiled base turns back toward the gate.
    # Only the short pair of photographed panels adjoining that corner is included.
    corners=[(-2.92,-.86),(-1.61,-.86),(-1.61,.002)]
    for side,(a,c) in enumerate(zip(corners,corners[1:])):
        p=np.asarray(a);v=np.asarray(c)-p;length=np.linalg.norm(v);d=v/length
        normal=np.array([-d[1],d[0]])
        rotation=[[d[0],d[1],0.],[normal[0],normal[1],0.],[0.,0.,1.]]
        def slab(label,at,span,offset,depth,z,h,material):
            xy=p+d*at+normal*offset
            b.box([*xy,z],[span,depth,h],material,basis=rotation,label=label)
        prefix='Street fence 'if side==0 else 'Returning fence '
        slab(prefix+'blockwork',length/2,length,.024,.158,.235,.47,JOINT)
        cols=round(length/.104);w=length/cols
        for row in range(7):
            for col in range(cols):
                slab(prefix+'tile course '+str(row+1),(col+.5)*w,w-.0035,-.063,.018,
                     (row+.5)*.064,.060,TILE)
        slab(prefix+'tile cap',length/2,length+.014,.012,.202,.468,.043,TILE)
        for j,h in enumerate((.58,1.55,1.67)):
            slab(prefix+'rail '+str(j+1),length/2,length,.015,.035,h,.027,IRON)
        count=round(length/.091)
        for j in range(count):
            centre=p+d*((j+.5)*length/count)
            x,y=centre
            box(b,prefix+'picket '+str(j+1),x-.008,x+.008,y-.008,y+.008,.481,1.692,IRON)
            b.lathe((x,y),[(1.678,.010),(1.701,.019),(1.737,.014),(1.786,.0012)],CAP,
                    segments=4 if lod else 8,label=prefix+'spearhead '+str(j+1))
    for i,(x,y) in enumerate(corners):
        box(b,'Fence solid post '+str(i+1),x-.024,x+.024,y-.024,y+.024,.461,1.72,IRON)

def masonry(b):
    # The right-hand wall continues beyond this surveyed detail. Brick faces,
    # beds and the short right edge are closed separately from the entrance.
    x0,x1=1.574,2.59
    z1=2.985
    box(b,'Right jamb bedding',x0,x1,.004,.236,.0,z1,MORTAR)
    h=.065;n=int(np.ceil(z1/h));w=.215
    for row in range(n):
        top=min((row+1)*h,z1);start=x0-w if row%2==0 else x0-w/2
        for j in range(8):
            x=start+j*w
            a=max(x+.0023,x0);c=min(x+w-.0023,x1)
            if c-a>.01:
                box(b,'Red brick face course '+str(row+1),a,c,-.009,.008,row*h+.002,top-.002,MATERIAL)
        # The exposed inner jamb turns at right angles to look into the passage.
        for j in range(2):
            y0=.013+j*.12;y1=min(y0+.116,.236)
            if y1>y0:box(b,'Red brick jamb return '+str(row+1),x0-.009,x0+.001,y0,y1,row*h+.002,top-.002,MATERIAL)
    box(b,'Dark frame at right wall head',x0-.004,x1+.007,-.022,.245,z1-.015,z1+.034,IRON)

def address(b,lod):
    # Only the large, legible 429弄 is reconstructed on this small enamel sign.
    x0,x1,z0,z1=1.888,2.478,2.563,2.767
    box(b,'Address plate enamel body',x0,x1,-.031,-.012,z0,z1,ENAMEL)
    marks={'4':[[(.65,.91),(.13,.42),(.85,.42)],[(.65,.91),(.65,.11)]],
           '2':[[(.16,.79),(.29,.91),(.61,.92),(.77,.78),(.76,.66),(.60,.52),(.16,.16),(.80,.16)]],
           '9':[[(.73,.58),(.55,.49),(.32,.52),(.19,.66),(.19,.81),(.35,.91),(.55,.90),(.73,.77),(.71,.41),(.60,.19),(.40,.11)]],
           '弄':[[(.17,.90),(.84,.90)],[(.23,.72),(.78,.72)],[(.50,.89),(.50,.53)],[(.12,.53),(.88,.53)],
                [(.08,.39),(.92,.39)],[(.34,.49),(.33,.26),(.27,.14),(.20,.08)],[(.68,.49),(.68,.09)]]}
    f=Facade(b,(-4,0),(4,0),'429 Lane address')
    for i,(char,strokes) in enumerate(marks.items()):
        for j,line in enumerate(strokes):
            coords=[(x0+.043+i*.113+.105*u,z0+.043+.132*v) for u,v in line]
            area=LineString(coords).buffer(.0063,quad_segs=2,cap_style='round',join_style='round')
            f.prism(area,.031,.0324,WHITE,'number '+str(i+1)+' stroke '+str(j+1))
    for x in (x0+.011,x1-.011):
        for z in (z0+.013,z1-.013):
            b.tube([(x,-.034,z),(x,-.03,z)],.0043,CAP,6 if lod else 10,'Enamel plate fasteners')

BOARD_FRAME='Bronze-coloured notice frame'
BOARD_FACE='Pale notice backing'
PALETTE.update({BOARD_FRAME:pigment([128,110,77],.54,.25), BOARD_FACE:pigment([194,196,182],.78)})

def notice_boards(b, measurements):
    # The 2021 view documents actual notice holders attached to both leaves.
    # The flat backing identifies their extent; no photographic artwork or writing is used.
    f=Facade(b,(-4,0),(4,0),'Temporary notice holders')
    for name,points in measurements['notice_holder_edges_px'].items():
        polygon=Polygon([position(u,v,-.039)[[0,2]] for u,v in points])
        inset=.025 if name!='East smaller' else .011
        union=polygon.buffer(-inset,join_style='mitre')
        edge=polygon.difference(union)
        f.prism(polygon,.019,.034,BOARD_FRAME,name+' backing')
        f.prism(edge,.034,.042,BOARD_FRAME,name+' metal rim')
        f.prism(union,.034,.036,BOARD_FACE,name+' plain insert')

def add_gate_surround(b,lod):
    measure=json.loads((MEASUREMENTS/'gate-frame-trace.json').read_bytes())
    top,z=bow(b,measure['upper_bow_xy'],'upper',lod)
    bow(b,measure['lower_bow_xy'],'lower',lod)
    post(b,float(top[0]),float(z[0]),0)
    post(b,float(top[-1]),float(z[-1]),1)
    discs=json.loads((MEASUREMENTS/'gate-medallions.json').read_bytes())
    for i,v in enumerate(discs['letters']):
        x,zc=v['centre_xz_m'];r=v['radius_m']
        box(b,'Sign backing strap '+str(i+1),x-.023,x+.023,.005,.041,zc-r-.034,zc+r+.045,CAP)
    side_fence(b,lod)
    masonry(b)
    address(b,lod)
    notice_boards(b,measure)
