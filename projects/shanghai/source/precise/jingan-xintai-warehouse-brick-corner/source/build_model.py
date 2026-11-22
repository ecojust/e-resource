"""Generate the two end bays photographed at 57 Xintai Road. Coordinates in metres."""
from pathlib import Path
import argparse
import os
import sys
from math import radians, sin, cos
import numpy as np
from PIL import Image
from shapely.geometry import box

SOURCE = Path(__file__).resolve().parent
PROJECT = next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import Builder
from xintai_brick_corner import add_warehouse_corner, arch, openings, F, MATERIALS, GREY, WIDTH, HEIGHT

ID = 'jingan-xintai-warehouse-brick-corner'
TITLE = '新泰仓库东翼红砖壁柱与两跨券窗'
META = dict(id=ID, name=TITLE, model_scope_zh='上海市静安区新泰路57号，东立面玻璃连接廊右手最外两跨。保留三层错高券窗、砖壁柱、首层玻璃门洞及端面短折墙。', viewer_page='xintai-warehouse-brick-corner.html',
            reference_height_m=11.40, heritage_register='4H001', all_dimensions_estimated=True, scope='East elevation. Two adjacent three-storey bays and a short return, based on post-renovation photographs.',
            geometry_license='MIT', texture_license='MIT', photos_embedded=False, third_party_models_embedded=False)
SASH='Window frame, dark painted steel'
EDGE='Inner frame, green-black glazing bead'
BRASS='Dark rubbed metal door pull'
THRESHOLD='Granite threshold and projecting door sill'
GLASS=['Window glass, '+n for n in ('blue sky','deep blue','neutral sky','shadow green','sunlit steel blue')]
BACK='Deep shadow behind the open sash'
TEXTURE=SOURCE/'blue-grey-bond.png'
def linear(rgb):
    x=np.asarray(rgb)/255.
    return np.where(x<=.04045,x/12.92,((x+.055)/1.055)**2.4).tolist()
def material(rgb,rough=.78,metal=0.):
    return dict(color=linear(rgb),roughness=rough,metallic=metal)
PALETTE={**MATERIALS,SASH:material([37,47,48],.52,.23),EDGE:material([49,61,58],.54,.12),
         BRASS:material([114,108,83],.48,.37),THRESHOLD:material([151,145,129]),BACK:material([36,43,43]),
         **{m:material(rgb,.32,.13)for m,rgb in zip(GLASS,([81,113,132],[39,66,82],[97,124,136],[54,69,65],[67,94,107]))}}
def make_texture():
    """Original scaled mortar and kiln colour. No source-image pixels are sampled."""
    width,height=600,912
    y,x=np.indices((height,width));u=x*WIDTH/width;z=HEIGHT-y*HEIGHT/height
    course=np.floor(z/.089).astype(int)
    step=np.where(course%6==0,.132,.244)
    horizontal=(u-(course%2)*step*.5)/step
    column=np.floor(horizontal).astype(int)
    tones=np.array([[107,121,116],[117,130,124],[124,133,123],[107,125,123],[133,142,133]])
    rgb=tones[(column*13+course*19+column*course)%5].astype(float)
    joint=(np.mod(z,.089)<.010)|(np.mod(horizontal,1)<.041)
    rgb[joint]=[138,143,133]
    rng=np.random.default_rng(488)
    rgb+=rng.normal(0,2.8,(height,width,1))
    Image.fromarray(np.clip(rgb,0,255).astype('uint8')).save(TEXTURE,optimize=True)

def transom_height(index):
    return (2.18,2.18,6.41,6.26,9.97,9.99)[index]

def add_frame(b,opening,index,far):
    c,base,h,spring,rise,th,red=opening
    name=f'Bay {1+index%2}, level {1+index//2}'
    opening_shape=arch(opening,32)[1]
    inset=.061 if index>1 else .075
    inner=opening_shape.buffer(-inset,join_style=2)
    def prism(shape,lo,hi,mat,label):
        b.prism(shape,lo,hi,F,mat,name+' '+label)
    prism(opening_shape.difference(inner),-.242,-.175,SASH,'outer steel frame')
    bead=inner.difference(inner.buffer(-.019,join_style=2))
    prism(bead,-.242,-.211,EDGE,'glass bead')
    clear=inner.buffer(-.019,join_style=2)
    high=clear.bounds[3]
    x0,x1=c-h,c+h
    level=index//2
    trans=transom_height(index)
    # The segmental transom is unbroken along the crown, above the flat rail.
    transom=clear.intersection(box(x0,trans+.029,x1,high+.01))
    prism(transom,-.255,-.244,GLASS[(index+1)%3],'curved transom glazing')
    bar=clear.intersection(box(x0,trans-.032,x1,trans+.032))
    prism(bar,-.246,-.176,SASH,'transom cross rail')
    # In the restored photograph the short openings carry small inset lights,
    # while each taller companion has three nearly vertical full-height lights.
    stations=[-.32,.33] if index%2 else [-.31,.31]
    if level==0:stations=[0.]
    limits=[-h]+stations+[h]
    for j,(a,d) in enumerate(zip(limits,limits[1:])):
        leaf=clear.intersection(box(c+a,base,c+d,trans-.032))
        if leaf.is_empty:continue
        tone=GLASS[3 if level==0 else (2*index+j)%len(GLASS)]
        swinging=(index==4 and j in (0,2))
        if swinging:
            prism(leaf,-.369,-.362,BACK,'recess behind projected light')
            hinge=trans-.033
            angle=radians(11)
            def tilt(x,z,depth):
                return (x,-depth-(hinge-z)*sin(angle),hinge-(hinge-z)*cos(angle))
            b.prism(leaf,-.254,-.245,tilt,tone,name+' tilted casement glass')
            b.prism(leaf.difference(leaf.buffer(-.029,join_style=2)),-.245,-.218,tilt,EDGE,name+' tilted casement frame')
        else:
            prism(leaf,-.263,-.248,tone,'pane '+str(j+1))
            if not far:
                prism(leaf.difference(leaf.buffer(-.019,join_style=2)),-.249,-.235,EDGE,'rebated pane '+str(j+1))
    for station in stations:
        bar=clear.intersection(box(c+station-.031,base,c+station+.031,trans-.030))
        prism(bar,-.251,-.185,SASH,'vertical dividing bar')
    if level==0:
        for shift in (-.109,.109):
            b.tube([(c+shift,.176,.90),(c+shift,.119,.94),(c+shift,.119,1.18),(c+shift,.176,1.20)],.012,BRASS,6 if far else 10,name+' door pull')
        b.box([c,-.022,.026],[h*2+.15,.322,.050],THRESHOLD,label=name+' stone threshold')
        for side in (-1,1):
            lower=clear.intersection(box(c+(side-1)*h,base+.076,c+(side+1)*h,base+.147))
            prism(lower,-.249,-.192,EDGE,'bottom door rail')
def add_building(b,lod=False):
    add_warehouse_corner(b,lod)
    for k,o in enumerate(openings()):add_frame(b,o,k,lod)
    # Material values in the original masonry measurements are sRGB swatches.
    for mat,spec in MATERIALS.items():
        b.palette[mat]['color']=linear(np.asarray(spec['color'])*255)
    b.palette[GREY].update(color=[1.,1.,1.],texture=str(TEXTURE))
    for p in b.parts:
        if p['material']==GREY:
            on_return='return' in p['label'].lower()
            p['texcoords']=[[min(1,max(0,(v[1] if on_return else v[0])/WIDTH)),min(1,max(0,1-v[2]/HEIGHT))]for v in p['vertices']]
if __name__=='__main__':
    make_texture()
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--mesh',type=Path);parser.add_argument('--far',action='store_true')
    args,rest=parser.parse_known_args()
    if args.mesh:
        if rest:parser.error('Unexpected options after --mesh')
        builder=Builder(PALETTE);add_building(builder,args.far);builder.save(args.mesh,META)
    else:
        sys.argv[1:]=rest
        from rebuild_warehouse import run
        run()
