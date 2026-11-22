"""Central upper window and open diamond railing observed at 394 Zhoushan Road."""
from math import sin,cos,pi
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import Polygon, LineString, box
from shapely.ops import unary_union
ID='hongkou-zhoushan-394-arched-window-and-diamond-balcony'
PEBBLE='Pebbled upright and arch surround'; WASH='Weathered upper plaster';FRAME='Painted wood window frames';GLASS='Window glass in shade';RAIL='Light cast geometric railing';CAP='Dark grey coping'; EDGE='Shadowed stone moulding'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(PEBBLE,[1,1,1],.98),(WASH,[1,1,1],.97),(RAIL,[1,1,1],.9),(FRAME,[.84,.823,.76],.75),(GLASS,[.33,.39,.43],.28),(CAP,[.33,.329,.29],.94),(EDGE,[.40,.37,.30],.93)]}
PIER=1.52;SPRING=2.72; openings=((-1.12,-.56),(-.48,-.034),(.034,.48),(.56,1.12))
def texture():
    f=Path(__file__).with_name('plaster-pebble-and-cast-stone.png')
    if not f.exists():
        rng=np.random.default_rng(683);h,w=250,295
        def noise(d):return np.asarray(Image.fromarray(rng.integers(0,255,d,dtype='uint8')).resize((w,h),Image.Resampling.BICUBIC),float)-128
        sand=noise((70,89))*.13+rng.normal(0,8,(h,w));wear=noise((31,25));patch=np.maximum(0,wear-36)*.40
        colors=[np.array([126,119,91])+sand[:,:,None],np.array([197,191,173])+(noise((7,13))*.064-patch)[:,:,None],np.array([186,182,157])+(noise((19,32))*.11+rng.normal(0,2.8,(h,w)))[:,:,None]]
        Image.fromarray(np.concatenate(colors,axis=1).clip(0,255).astype('uint8')).quantize(224).save(f)
    for m in (PEBBLE,WASH,RAIL):PALETTE[m]['texture']=str(f)
def rim(rx,rz,angles): return [(rx*cos(a),SPRING+rz*sin(a))for a in angles]
def add_building(b,far=False):
    texture()
    def piece(poly,front,back,mat,name):
        start=len(b.parts);b.prism(poly,-back,-front,lambda x,z,d:(x,-d,z),mat,name)
        if mat in (PEBBLE,WASH,RAIL):
            band=(PEBBLE,WASH,RAIL).index(mat)
            for part in b.parts[start:]:part['texcoords']=[((band+.015+.97*max(0,min(1,(x+1.70)/3.40)))/3,.993-.988*max(0,min(1,z/4.21)))for x,d,z in part['vertices']]
    def block(x,z,xx,zz,f,r,m,n):piece(box(x,z,xx,zz),f,r,m,n)
    angles=np.linspace(0,pi,17 if far else 41)
    def band(rx,rz,w,h,front,back,m,n):piece(Polygon(rim(rx,rz,angles)+rim(rx-w,rz-h,angles[::-1])),front,back,m,n)
    wall=Polygon([(-1.30,.16),(1.30,.16),*rim(1.30,.99,angles),(-1.30,.16)])
    windows=unary_union([box(x,.33,xx,2.68)for x,xx in openings]);piece(wall.difference(windows),.12,.33,WASH,'Recessed plaster tympanum and wall between the wooden lights')
    band(1.565,1.40,.223,.29,-.045,.338,PEBBLE,'Broad curved pebble-finished surround');band(1.38,1.12,.087,.113,-.076,.255,EDGE,'Inner shadow moulding');band(1.627,1.493,.085,.10,-.127,.383,CAP,'Projecting curved hood and lower shadow edge')
    for s in (-1,1):
        cx=s*1.44;block(cx-.114,0,cx+.114,SPRING,-.038,.335,PEBBLE,'Pebbled side jamb');block(cx-.135,2.57,cx+.135,2.694,-.085,.35,EDGE,'Moulded impost line');block(cx-.16,2.686,cx+.16,2.746,-.105,.373,CAP,'Dark upper impost')
    for i,(x,xx) in enumerate(openings):
        mid=(x+xx)/2
        block(x,.33,xx,2.68,.183,.21,GLASS,'Glass of photographed window '+str(i+1))
        for r in (x,xx):block(r-.032,.31,r+.032,2.71,.021,.17,FRAME,'Full-height painted wood stile')
        for z in (.332,2.08,2.677):block(x,z-.036,xx,z+.036,.02,.174,FRAME,'Sill head or wide rail between lights')
        block(mid-.014,.34,mid+.014,2.665,.055,.16,FRAME,'Narrow vertical glazing bar')
        for z in (.67,1.03,1.39,1.74,2.38):block(x+.01,z-.016,xx-.01,z+.016,.052,.16,FRAME,'Horizontal glazing bar')
    block(-1.48,.02,1.48,.13,-.692,.339,EDGE,'Projecting balcony floor');block(-1.49,.12,1.49,.175,-.693,.31,RAIL,'Light lip of balcony slab');block(-1.47,.12,1.47,.173,-.697,-.52,CAP,'Front drip line')
    bars=[box(-1.451,.208,1.451,.266),box(-1.451,.407,1.451,.447),box(-1.451,.673,1.451,.708),box(-1.451,.752,1.451,.797)]
    for j in range(6):
        cx=(j-2.5)*.47
        poly=LineString([(cx,.355),(cx+.178,.539),(cx,.698),(cx-.178,.539),(cx,.355)]).buffer(.029,cap_style=2,join_style=2)
        bars.extend([poly,box(cx-.021,.224,cx+.021,.362),box(cx-.021,.695,cx+.021,.76)])
    for j in range(5):
        x=(j-2)*.47;bars.append(box(x-.027,.224,x+.027,.792))
    for side in (-1,1):
        cx=side*1.427;bars.append(box(cx-.049,.179,cx+.049,.783));block(cx-.046,.204,cx+.046,.799,-.60,.06,RAIL,'Solid cheek at balcony return')
    piece(unary_union(bars),-.625,-.546,RAIL,'Cast apertures around six repeating diamonds')
    block(-1.489,.799,1.489,.859,-.665,-.503,CAP,'Continuous weathered handrail above the open band')
    if not far:
        for x,xx in openings:
            for side in (x,xx):block(side-.010,.34,side+.010,2.66,.011,.021,FRAME,'Edge bead of each outer frame')
