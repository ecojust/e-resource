"""No.51 garden gate with separate editable iron leaves, inscribed plate, stone piers and lamps."""
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

SOURCE = Path(__file__).resolve().parent
MEASURE = SOURCE.parent / 'measurements'
PLANE = json.loads((MEASURE / 'gate-plane-and-inscription.json').read_text())
SURVEY = json.loads((MEASURE / 'gate-iron-profiles.json').read_text())
PIER = 'No.51 | pink and black speckled granite'
PALE = 'No.51 | pale grey granite bands'
DARK = 'No.51 | dark polished granite cornices'
STEEL = 'No.51 | dark brown-black wrought steel'
BRASS = 'No.51 | aged brass street-number plate'
INK = 'No.51 | dark recessed address strokes'
GLOW = 'No.51 | cool frosted lantern panels'
CAP = 'No.51 | patinated dark lamp cap'

def finish(rgb, roughness, metallic=0.):
    c=np.array(rgb,dtype=float)/255
    linear=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    return dict(color=linear.tolist(), roughness=roughness, metallic=metallic)

PALETTE={
    PIER:dict(color=[1.,1.,1.], texture=str(SOURCE/'gate-granite.jpg'), roughness=.60, metallic=.05),
    PALE:finish((146,137,124),.73), DARK:finish((90,64,58),.52,.09),
    STEEL:finish((64,48,43),.56,.38),BRASS:finish((172,144,91),.46,.53),
    INK:finish((52,43,34),.54,.17),GLOW:finish((170,178,169),.45),
    CAP:finish((67,68,64),.51,.37),
}
SX=6.18/840
SZ=3.75/510
def x_at(u):return -3.10+u*SX
def z_at(v):return 3.65-v*SZ

def box(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box(((x0+x1)*.5,(y0+y1)*.5,(z0+z1)*.5),(x1-x0,y1-y0,z1-z0),mat,label=label)

def plate(b,polygon,y,thickness,material,label):
    if polygon.is_empty:return
    polygon=polygon.buffer(0)
    b.prism(polygon,-y-thickness,-y,lambda x,z,d:(x,-d,z),material,label)

def rect(b,u0,u1,vtop,vbottom,y,depth,mat,label):
    box(b,x_at(u0),x_at(u1),y,y+depth,z_at(vbottom),z_at(vtop),mat,label)

def interp(points,steps=4):
    pts=np.array(points,float)
    if len(pts)<3:return pts
    result=[pts[0]]
    for i in range(len(pts)-1):
        a=pts[max(0,i-1)];q=pts[i];r=pts[i+1];s=pts[min(len(pts)-1,i+2)]
        for t in np.arange(1,steps+1)/steps:
            result.append(.5*((2*q)+(-a+r)*t+(2*a-5*q+4*r-s)*t*t+(-a+3*q-3*r+s)*t*t*t))
    return np.asarray(result)

def ribbon(points,width,far):
    uv=interp(points,2 if far else 4)
    return LineString([(x_at(u),z_at(v)) for u,v in uv]).buffer(width/2,quad_segs=2,cap_style='round',join_style='round')

def transformed(path,u,v,sx=1.,sy=1.):
    return [(u+x*sx,v+y*sy)for x,y in path]

def ironwork(b,far):
    d=SURVEY;s=d['scrolls'];top=np.array(d['top_rail_centres'])
    for idx,(lo,hi) in enumerate(d['spans']):
        name=('Left garden drive leaf' if idx==0 else 'Right leaf with wicket')
        uc=np.linspace(lo,hi,19 if far else 37)
        vs=np.interp(uc,top[:,0],top[:,1])
        steel=Polygon([(x_at(u),z_at(v-4.3))for u,v in zip(uc,vs)]+[(x_at(u),z_at(v+4.3))for u,v in zip(uc[::-1],vs[::-1])])
        plate(b,steel,-.025,.061,STEEL,name+' | shallow bent top rail')
        for k,(v0,v1) in enumerate(d['gallery_rails']):
            if idx==1 and k==1:lo0=d['wicket']['right']
            else:lo0=lo
            rect(b,lo0,hi,v0,v1,-.022,.052,STEEL,name+' | horizontal rail '+str(k+1))
        for k,u in enumerate(d['bars'][idx],1):
            upper=225. if idx==0 or u>568 else 209.
            rect(b,u-2.2,u+2.2,upper,493.,-.005,.030,STEEL,name+' | upright '+str(k))
        for edge,(u0,u1) in enumerate((d['meeting_stiles'][idx],(lo,lo+5)if idx==0 else(hi-5,hi))):
            vmax=float(np.interp((u0+u1)/2,top[:,0],top[:,1]))
            rect(b,u0,u1,vmax,493.,-.029,.073,STEEL,name+' | vertical frame '+str(edge+1))
    # A continuous metal hand pull appears on the left, separate from the right leaf's inset wicket.
    pull=d['pull'];rect(b,pull['left'],pull['right'],pull['v']-1.1,pull['v']+1.1,-.057,.023,STEEL,'Drive leaf | long rectangular pull')
    rect(b,375,384,pull['plate_top'],pull['plate_bottom'],-.055,.034,STEEL,'Drive leaf | lock stile escutcheon')
    wicket=d['wicket']
    for u in (wicket['left'],wicket['right']-wicket['frame_width']):
        rect(b,u,u+wicket['frame_width'],wicket['top'],493,-.042,.074,STEEL,'Inset pedestrian gate | upright')
    rect(b,wicket['left'],wicket['right'],wicket['top']-1,wicket['top']+8,-.043,.075,STEEL,'Inset pedestrian gate | head frame')
    for i,u in enumerate(d['top_spears_x']):
        base=np.interp(u,top[:,0],top[:,1])-3.8
        size=.93 if i in (0,11) else 1.
        origin=base-24*size
        forms=[ribbon(transformed(s['spear']['stem'],u,origin,size,size),.010,far)]
        shape=Polygon([(x_at(x),z_at(v))for x,v in transformed(s['spear']['blade'],u,origin,size,size)])
        forms.append(shape)
        for side in (-1,1):
            forms.append(ribbon(transformed(s['spear']['side'],u,origin,size*side,size),.009,far))
        plate(b,unary_union(forms),-.017,.017,STEEL,'Rolled rail | pierced fleur finial '+str(i+1))
    for index,(u,side,scale) in enumerate([(259,-1,.96),(407,-1,.84),(434,1,.94),(584,1,.90)]):
        name='Face gallery | large scrolled leaf '+str(index+1)
        forms=[]
        for key,path in s['large'].items():
            uv=transformed(path,u,191.3,scale*side,scale)
            if key=='flower':forms.append(Polygon([(x_at(x),z_at(y))for x,y in uv]))
            else:forms.append(ribbon(uv,.013 if key=='main' else .010,far))
        plate(b,unary_union(forms),-.018,.020,STEEL,name)
    for j,(u,side) in enumerate([(158,1),(195,-1),(296,1),(359,-1),(481,1),(523,1),(626,1)]):
        form=ribbon(transformed(s['small'],u,191.4,side,1),.010,far)
        plate(b,form,-.018,.015,STEEL,'Face gallery | small return '+str(j+1))
    for i,(l,r) in enumerate(((115,411),(567,662))):
        n=round((r-l)/29.0);step=(r-l)/n
        for k in range(n):
            cx=l+(k+.5)*step
            halves=[ribbon(transformed(s['middle'],cx,217.8,sign*step/34.,.98),.0095,far)for sign in (-1,1)]
            plate(b,unary_union(halves),-.018,.017,STEEL,'Middle rail '+str(i+1)+' | paired C volutes '+str(k+1))
    for i,bar_centres in enumerate(d['bars']):
        for k,(l,r) in enumerate(zip(bar_centres[:-1],bar_centres[1:])):
            if i and l<560<r:continue
            cx=(l+r)*.5
            v0=224 if i==0 or cx>568 else 209
            design=[ribbon(transformed(s['hanging'],cx,v0,sign*(r-l)/18.,.9),.0086,far)for sign in (-1,1)]
            plate(b,unary_union(design),-.013,.0145,STEEL,'Lower rail '+str(i+1)+' | pendant scroll pair '+str(k+1))
    for k,v in enumerate(np.arange(242,444,21)):
        uv=transformed(s['middle'],391.2,v,.70,-.68)
        plate(b,ribbon(uv,.009,far),-.012,.016,STEEL,'Lock side | upright scrolling '+str(k+1))
    for side in (-1,1):
        # The central and side feet physically meet their own half of the curved upper rail.
        for foot in (3.,33.):
            u=425+side*foot
            rect(b,u-1.3,u+1.3,107.7,float(np.interp(u,top[:,0],top[:,1])), -.016,.020,STEEL,'Crest | welded foot')
        forms=[]
        for key,path in s['crown'].items():
            uv=transformed(path,425,110,side,1.)
            forms.append(Polygon([(x_at(x),z_at(y))for x,y in uv]) if key=='leaves' else ribbon(uv,.014 if key=='central'else .011,far))
        plate(b,unary_union(forms),-.018,.023,STEEL,('Left'if side<0 else'Right')+' leaf | central crest')

def stepped_block(b,cx,cy,sections,mat,label):
    vertices=[]; faces=[]
    for z,w,d in sections:
        vertices.extend((cx+sx*w*.5,cy+sy*d*.5,z) for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1)))
    faces.append((3,2,1,0))
    for j in range(len(sections)-1):
        for i in range(4):
            a=4*j+i;c=4*j+(i+1)%4;faces.append((a,c,c+4,a+4))
    k=4*(len(sections)-1);faces.append((k,k+1,k+2,k+3))
    b.add(vertices,faces,mat,label)

def lantern(b,cx,cy,z,far):
    name='No.51 pier lantern | '
    stepped_block(b,cx,cy,[(z,.125,.125),(z+.028,.125,.125),(z+.051,.080,.080)],CAP,name+'shoe')
    stepped_block(b,cx,cy,[(z+.047,.065,.065),(z+.128,.13,.13),(z+.148,.130,.130)],CAP,name+'tapered foot')
    stepped_block(b,cx,cy,[(z+.143,.126,.126),(z+.370,.205,.205)],GLOW,name+'four frosted lens panes')
    for sx in (-1,1):
        for sy in (-1,1):
            b.tube([(cx+sx*.064,cy+sy*.064,z+.141),(cx+sx*.106,cy+sy*.106,z+.377)],
                   .0082,CAP,4,name+'splayed metal corner')
    stepped_block(b,cx,cy,[(z+.368,.206,.206),(z+.380,.239,.239),(z+.394,.239,.239),
                  (z+.405,.219,.219),(z+.435,.127,.127),(z+.478,.042,.042)],CAP,name+'hipped metal lid')
    b.lathe((cx,cy),[(z+.472,.018),(z+.501,.022),(z+.520,.010)],CAP,8 if far else 12,name+'finial')

def gateposts(b,far):
    # The image clips the outer front corner of the left pier. Its return is wholly legible;
    # its across-street width follows the separately visible right pier.
    front_y=PLANE['post_depth_observations']['adopted_front_y_m'];depth=-front_y+.018
    for side,lo,hi in [('left',-3.115,-2.277),('right',2.157,2.996)]:
        name=side.capitalize()+' granite gatepost | ';cx=(lo+hi)*.5;cy=(front_y+.018)*.5
        for j,(z0,z1,mat) in enumerate(((0.,.32,PIER),(.32,.45,PALE),(.45,1.09,PIER),
                (1.09,1.235,PALE),(1.235,1.919,PIER),(1.919,2.071,PALE),(2.071,2.772,PIER))):
            box(b,lo,hi,front_y,.018,z0,z1,mat,name+'course '+str(j+1))
        w=hi-lo
        profile=[(2.768,w+.008,depth+.008),(2.791,w+.024,depth+.024),(2.814,w+.024,depth+.024),
                 (2.836,w+.073,depth+.073),(2.850,w+.079,depth+.079),(2.869,w+.048,depth+.048),
                 (2.888,w+.035,depth+.035),(2.912,w+.088,depth+.088),(2.941,w+.105,depth+.105),
                 (2.956,w+.102,depth+.102),(2.969,w+.047,depth+.047)]
        stepped_block(b,cx,cy,profile,DARK,name+'stepped cornice and drip')
        lantern(b,cx,cy,2.969,far)
    # Straight cylindrical ends inside the hinges continue behind the right jamb in the source photograph.
    for k,v in enumerate((194.,222.)):
        rect(b,661.,(2.166+3.10)/SX,v-2.4,v+2.4,-.012,.041,STEEL,'Right leaf | concealed straight frame to hinge '+str(k+1))
    # A plain, short continuation of the bent top rail is visible at the edge of the right post.
    path=[(661.,156.),((2.166+3.10)/SX,170.)]
    plate(b,ribbon(path,.062,far),-.016,.053,STEEL,'Right leaf | return of intermediate rail into jamb')

def sign(b,far):
    data=PLANE['plate'];points=np.array(data['rectified_dimensions_measured_on_Y_pillar_front'])
    l,bottom=points.min(axis=0);r,top=points.max(axis=0)
    y=data['registered_plane_y_m']-.014
    box(b,l,r,y,y+.019,bottom,top,BRASS,'Street-side right pier | brass address tablet')
    tw,th=data['raster_size_px']
    def at(pair):
        u,v=pair;return l+u*(r-l)/tw,top-v*(top-bottom)/th
    for i,record in enumerate(data['lettering']):
        outer=[at(pair) for pair in record['outline']]
        holes = []
        outer_line = LineString([*outer, outer[0]])
        for hole in record['holes']:
            ring = Polygon([at(pair) for pair in hole])
            # A photographed dark counter shares a single source pixel with its outline.
            # Preserve the counter and leave a subpixel-wide web at that contact.
            if ring.distance(outer_line) < .00005:
                ring = ring.buffer(-.00027, join_style='mitre')
            holes.append(list(ring.exterior.coords))
        outline=Polygon(outer,holes).buffer(0).buffer(-.00028,join_style='mitre').buffer(.00028,join_style='mitre').simplify(.00018)
        if not outline.is_empty:
            plate(b,outline,y-.0019,.0021,INK,'Address tablet | measured inscription stroke group '+str(i+1))
    rim=[(l+.014,bottom+.016),(r-.014,bottom+.016),(r-.014,top-.016),(l+.014,top-.016),(l+.014,bottom+.016)]
    plate(b,LineString(rim).buffer(.0009,quad_segs=1),y-.0015,.0018,INK,'Address tablet | dark rectangular engraved border')

def add_local_gate(b,lod=False):
    far=lod is True or lod in ('lod','low','distant')
    b.palette.update(PALETTE)
    first=len(b.parts)
    ironwork(b,far)
    gateposts(b,far)
    sign(b,far)
    for part in b.parts[first:]:
        if part['material']==PIER:
            uv=np.array([(x+.64*y,z+.48*y)for x,y,z in part['vertices']])
            part['texcoords']=((uv-uv.min(axis=0))/np.maximum(np.ptp(uv,axis=0),1e-9)).tolist()

def add_court_gate(b,lod=False):
    """Install the independent garden gate in the central-column house coordinate frame."""
    placement=json.loads((MEASURE/'garden-gate-placement.json').read_text());matrix=np.array(placement['gate_to_house'])
    first=len(b.parts);add_local_gate(b,lod)
    for part in b.parts[first:]:
        v=np.asarray(part['vertices'])
        placed=v@matrix[:3,:3].T+matrix[:3,3]
        # Only straight ends below the lowest photographed gatework are extrapolated to the paving.
        floor=placement['physical_grade']
        if part['material'] in (PIER,STEEL):
            bottom=v[:,2]<.037
            placed[bottom,2]=floor['finished_post_base_house_z_m'] if part['material']==PIER else floor['finished_iron_clearance_house_z_m']
        part['vertices']=placed.tolist()
