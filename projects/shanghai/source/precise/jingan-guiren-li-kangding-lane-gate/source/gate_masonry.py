"""Kangding East Road passage, two adjacent bays, and their source-visible returns."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parent
LAYOUT=json.loads((ROOT.parent/'measurements/gate-layout.json').read_text())
OPENINGS=LAYOUT['openings']
EDGE=LAYOUT['front_edges']
P=LAYOUT['passage']
GREY='Guiren | grey running-bond brick'
RED='Guiren | russet band brick'
PLASTER='Guiren | grey mineral rendering'
STONE='Guiren | pale sill and projecting caps'
PIER='Guiren | smooth entrance piers'
REVEAL='Guiren | sheltered passage plaster'
PAVING='Guiren | worn threshold aggregate'
COVER='Guiren | inset pavement panel'
COVER_RIB='Guiren | pale tread rib'
GALLERY='Guiren | grey enclosed balcony panels'
METAL='Guiren | folded sheet fascia'
JOINERY='Guiren | dark door joinery'
GLASS='Guiren | sheltered door transom'
NUMBER='Guiren | green address plate'
RIM='Guiren | green enamel edge'

def material(srgb,rough=.87,texture=None,*,metal=0.):
    v=np.array(srgb)/255
    p={'color':np.where(v<=.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),'roughness':rough,'metallic':metal}
    if texture:p['texture']=str(ROOT/texture)
    return p
PALETTE={GREY:material((255,255,255),texture='guiren-grey-brick.jpg'),RED:material((255,255,255),texture='guiren-russet-brick.jpg'),
    PLASTER:material((153,146,132)),STONE:material((174,166,146)),PIER:material((121,120,111)),REVEAL:material((131,128,114)),
    COVER:material((114,116,110),.77,metal=.23),COVER_RIB:material((159,159,148),.67,metal=.20),
    PAVING:material((129,126,115)),GALLERY:material((139,141,132)),METAL:material((111,114,106),.69,metal=.14),
    JOINERY:material((105,53,43)),GLASS:material((67,83,77),.33,metal=.11),NUMBER:material((255,255,255),.68,'guiren-address-plate.png'),RIM:material((65,89,72),.64,metal=.16)}

def solid(b,label,x0,x1,y0,y1,z0,z1,mat):
    if min(x1-x0,y1-y0,z1-z0)<=.00001:return
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)

def wall(b,label,field,front,back,mat):
    if not field.is_empty:
        b.prism(field,-back,-front,lambda x,z,depth:(x,-depth,z),mat,label)

def opening(key):
    a=OPENINGS[key]
    return box(a['x'][0],a['z'][0],a['x'][1],a['z'][1])

def sill(b,label,l,r,z,face,mat):
    solid(b,label+' | sill bed',l-.065,r+.065,face-.055,face+.045,z-.095,z-.038,mat)
    solid(b,label+' | sill nosing',l-.093,r+.093,face-.106,face+.038,z-.05,z-.008,mat)

def street_number(b):
    # This address plate sits on the entrance beam, below the older three-character plaque.
    cx,cz=-.100,3.64;half=.270;hh=.080
    solid(b,'Lane number | enamel back and return',cx-half-.008,cx+half+.008,-.108,-.088,cz-hh-.007,cz+hh+.007,RIM)
    corners=[(cx-half,cz-hh),(cx+half,cz-hh),(cx+half,cz+hh),(cx-half,cz+hh)]
    vertices=[(x,y,z) for y in (-.109,-.1075) for x,z in corners]
    faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    b.add(vertices,faces,NUMBER,'Lane number | 3弄3-14号 康定东路')
    # The printed front uses the full original drawing. Back vertices pick an unlettered green patch.
    b.parts[-1]['texcoords']=[(0,1),(1,1),(1,0),(0,0),(.052,.70),(.085,.70),(.085,.60),(.052,.60)]

def gate(b,lod):
    l,r=EDGE['gate_left'],EDGE['gate_right'];e=LAYOUT['crown'];cl,cr=e['central_left'],e['central_right']
    shoulder=e['shoulder_top'];crest=e['central_top'];ledge=.20
    field=Polygon([(l,0),(r,0),(r,shoulder-ledge),(cr,shoulder-ledge),(cr,crest-ledge),
                  (cl,crest-ledge),(cl,shoulder-ledge),(l,shoulder-ledge)])
    arch=box(P['left'],0,P['right'],P['lintel_soffit'])
    wall(b,'Overgate | cut plaster street face',field.difference(unary_union([arch,opening('gate_upper')])),0,.34,PLASTER)
    for a,c,z,label in [(l,cl,shoulder,'east shoulder'),(cl,cr,crest,'raised centre'),(cr,r,shoulder,'west shoulder')]:
        solid(b,'Gable | '+label+' fascia',a-.043,c+.043,-.065,.37,z-.22,z-.12,PLASTER)
        solid(b,'Gable | '+label+' lower lip',a-.082,c+.082,-.122,.40,z-.131,z-.078,STONE)
        solid(b,'Gable | '+label+' coping',a-.113,c+.113,-.174,.43,z-.082,z,STONE)
        if not lod:solid(b,'Gable | '+label+' shadow bead',a-.076,c+.076,-.096,-.059,z-.165,z-.139,REVEAL)
    z=P['lintel_soffit'];l0=P['left'];r0=P['right']
    for x0,x1,tag in [(l,l0,'east'),(r0,r,'west')]:
        solid(b,'Gate | '+tag+' flat pier',x0,x1,-.048,.33,0,z,PIER)
        # A dark stone pad, square capital and a narrow raised contact beneath the beam.
        solid(b,'Gate | '+tag+' foot',x0-.014,x1+.015,-.066,.35,0,.125,PIER)
        solid(b,'Gate | '+tag+' abacus',x0-.035,x1+.03,-.095,.35,z-.158,z-.072,STONE)
        solid(b,'Gate | '+tag+' outer cap',x0-.052,x1+.04,-.115,.37,z-.073,z-.006,PIER)
    solid(b,'Gate | squared lintel',l-.028,r+.025,-.073,.38,z,P['beam_top'],PIER)
    solid(b,'Gate | projecting beam head',l-.044,r+.045,-.129,.40,3.832,3.925,STONE)
    solid(b,'Gate | fine top drip',l-.058,r+.058,-.153,.408,3.923,3.968,STONE)
    sill(b,'Gate upper casement',-.68,.79,5.13,0,PIER)
    solid(b,'Gate upper casement | lintel',-.78,.89,-.077,.055,6.84,6.982,PIER)
    solid(b,'Gate upper casement | projecting hood',-.86,.97,-.17,.06,6.963,7.053,STONE)
    for x0,x1 in [(-.76,-.68),(.79,.87)]:
        solid(b,'Gate upper casement | jamb',x0,x1,-.046,.08,5.14,6.86,PIER)
    street_number(b)
    depth=P['visible_depth']
    solid(b,'Passage | east reveal continuing inside',l0-.19,l0,.33,depth,.012,z,REVEAL)
    solid(b,'Passage | west reveal continuing inside',r0,r0+.19,.33,depth,.012,z,REVEAL)
    solid(b,'Passage | first-floor soffit',l0-.19,r0+.19,.33,depth,z,z+.21,REVEAL)
    solid(b,'Passage | open threshold and lane floor',l0-.21,r0+.21,-.18,P['paving_length'],-.055,.008,PAVING)
    # Street-side entrance and inner termination stay open at grade.
    for yy in [.15,1.54,3.18]:
        solid(b,'Passage | flagstone joint',l0,r0,yy,yy+.009,.008,.010,REVEAL)

def paving_cover(b,lod):
    q=np.array(LAYOUT['pavement_cover']['visible_corners_xy'])
    b.plan_prism(Polygon(q),.008,.018,COVER,'Passage | rectangular panel in photographed paving')
    # The clipped left boundary is the last edge visible past the iron grille.
    # Bright longitudinal strips repeat at about 16/200 of the visible width.
    def point(u,v):
        back=q[0]+u*(q[1]-q[0]);front=q[3]+u*(q[2]-q[3])
        return front*(1-v)+back*v
    for i in range(12):
        u=(i+.50)/12.5
        span=.010 if lod else .008
        poly=Polygon([point(u-span,.055),point(u+span,.055),point(u+span,.958),point(u-span,.958)])
        b.plan_prism(poly,.018,.021,COVER_RIB,'Passage | parallel tread rib')
    if not lod:
        rim=Polygon(q).difference(Polygon(q).buffer(-.015,join_style='mitre'))
        b.plan_prism(rim,.018,.022,COVER_RIB,'Passage | panel edging')

def east(b,lod):
    l,r=EDGE['east_cut'],EDGE['gate_left']
    holes=unary_union([opening(k)for k in ('left_lower','left_upper')])
    field=box(l,0,r,7.88)
    wall(b,'East bay | grey brick wall with cut openings',field.difference(holes),0,.33,GREY)
    for j,(lo,hi) in enumerate(LAYOUT['east_brick']['red_intervals_m']):
        wall(b,'East bay | running red band %02d'%(j+1),box(l,lo,r,hi).difference(holes),-.006,.004,RED)
    for tag in ('left_lower','left_upper'):
        a=OPENINGS[tag];xl,xr=a['x'];z0,z1=a['z']
        sill(b,'East '+tag,xl,xr,z0,0,RED)
        if not lod:
            for x0,x1 in [(xl-.054,xl),(xr,xr+.054)]:
                solid(b,'East '+tag+' | brick reveal edge',x0,x1,-.015,.036,z0,z1,RED)
        solid(b,'East '+tag+' | red brick lintel',xl-.071,xr+.071,-.016,.105,z1,z1+.080,RED)
    solid(b,'East bay | projecting floor beam',l,r,-.052,.36,3.454,3.54,RED)
    solid(b,'East bay | weathering ledge',l,r,-.097,.385,3.736,3.835,RED)
    solid(b,'East bay | parapet edge',l,r,-.085,.38,7.795,7.89,PIER)
    solid(b,'East bay | end return',l,l+.16,.33,1.05,0,7.84,GREY)

def west(b,lod):
    l,r=EDGE['gate_right'],EDGE['west_cut'];a=OPENINGS['right_upper'];gx=a['y'];xt0,xt1=a['transom_x'];top=a['transom_z']
    lower=OPENINGS['right_lower'];ly=lower['y'];door=(2.38,3.54,3.04)
    openings=unary_union([opening('right_lower'),box(door[0],0,door[1],door[2])])
    wall(b,'West bay | ground wall around door and four sashes',box(l,0,r,3.53).difference(openings),ly,ly+.30,GALLERY)
    xl,xr=lower['x'];sill(b,'West lower sashes',xl,xr,lower['z'][0],ly,JOINERY)
    solid(b,'West dwelling | timber entrance leaf',door[0]+.018,door[1]-.018,ly+.100,ly+.156,.025,2.46,JOINERY)
    solid(b,'West dwelling | rectangular glazed overlight',door[0]+.07,door[1]-.07,ly+.12,ly+.148,2.48,2.96,GLASS)
    for x in [door[0],door[1]-.065]:
        solid(b,'West dwelling | door jamb',x,x+.065,ly+.034,ly+.137,.018,3.04,JOINERY)
    solid(b,'West dwelling | transom bar',door[0],door[1],ly+.03,ly+.138,2.43,2.49,JOINERY)
    solid(b,'West dwelling | door head',door[0],door[1],ly+.03,ly+.138,2.96,3.04,JOINERY)
    front=box(l,3.55,r,7.41)
    upper_clear=unary_union([opening('right_upper'),box(xt0,a['z'][1],xt1,top)])
    wall(b,'West bay | enclosed timber gallery and panel spandrels',front.difference(upper_clear),gx,gx+.13,GALLERY)
    for x0,x1 in [(l,l+.12),(r-.12,r)]:
        solid(b,'Gallery | side return',x0,x1,gx+.13,.20,3.61,7.38,GALLERY)
    solid(b,'Gallery | balcony floor and soffit',l,r,gx-.065,.32,3.46,3.58,GALLERY)
    for z,h,pr in [(3.54,.10,.087),(4.80,.075,.045),(7.26,.06,.05),(7.36,.12,.105)]:
        solid(b,'Gallery | horizontal folded trim',l-.018,r+.018,gx-pr,gx+.045,z,z+h,METAL)
    solid(b,'Gallery | upper return behind fascia',l,r,gx+.13,.34,7.33,7.43,METAL)
    for x in [l+.05,xt0-.035,xt1+.012,r-.066]:
        solid(b,'Gallery | vertical panel seam',x,x+.024,gx-.016,gx+.01,3.65,7.26,METAL)
    if not lod:
        for x in [2.61,3.44,4.26,5.08,5.91]:
            solid(b,'Gallery | apron joint',x,x+.012,gx-.012,gx+.011,3.65,4.78,METAL)

def physical_uv(part):
    # Choose the two metric axes spanning each face. Jambs keep a finite UV area too.
    old=part['vertices'];chart={};xyz=[];uv=[];tri=[]
    for face in part['triangles']:
        a,b,c=(np.asarray(old[j])for j in face)
        axis=int(np.argmax(np.abs(np.cross(b-a,c-a))))
        axes=((1,2),(0,2),(0,1))[axis];new=[]
        for i in face:
            token=(i,axis)
            if token not in chart:
                chart[token]=len(xyz);p=old[i];xyz.append(p);uv.append((p[axes[0]]/1.47,p[axes[1]]/.864))
            new.append(chart[token])
        tri.append(tuple(new))
    part.update(vertices=xyz,triangles=tri,texcoords=uv)

def add_street_masonry(builder,lod=False):
    start=len(builder.parts);east(builder,lod);gate(builder,lod);paving_cover(builder,lod);west(builder,lod)
    for part in builder.parts[start:]:
        if part['material'] in (GREY,RED):physical_uv(part)
