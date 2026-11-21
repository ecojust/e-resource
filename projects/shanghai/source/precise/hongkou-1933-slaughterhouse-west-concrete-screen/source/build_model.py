"""Build the photographed western arcade and pierced concrete screens of the 1933 Shanghai abattoir."""
import argparse,hashlib,json,os,struct,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as RepeatingTextureBuilder
from photo_architecture import Facade
from shapely.geometry import box
from aggregate_finish import CAST,TEXTURE,apply_metric_uv
from pierced_screens import DARK,EDGE,GLASS_ALPHA,LOW,METAL,MID,PALE,SHADE,screen
from skyline import centre_head,regular_head,side_louvres,terrace
from street_arcade import DRESS,FLOOR,INSET,LETTER,SOFFIT,arcade,pier

ID='hongkou-1933-slaughterhouse-west-concrete-screen'
META=dict(id=ID,name='1933老场坊西立面圆环花格窗',heritage_group='4F011',viewer_page='slaughterhouse-west-concrete-screen.html',
          scope='沙泾路10号原工部局宰牲场西立面。普通八跨各两扇花窗与中央双窄屏、下部门廊和两端收边。')
DIM=json.loads((SOURCE/'dimensions.json').read_bytes())


class AggregateBuilder(RepeatingTextureBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata);p=Path(path);side=p.with_suffix('.geometry.json')
        blob=p.read_bytes()
        size=struct.unpack_from('<I',blob,12)[0]
        scene=json.loads(blob[20:20+size])
        panes=[m for m in scene['materials'] if m['name'] in GLASS_ALPHA]
        assert len(panes)==3
        for material in panes:
            assert material['alphaMode']=='BLEND'
            material['doubleSided']=True
        block=json.dumps(scene,ensure_ascii=True,separators=(',',':')).encode()
        block+=b' '*(-len(block)%4)
        binary=blob[20+size:]
        p.write_bytes(struct.pack('<4sIIII',b'glTF',2,20+len(block)+len(binary),len(block),0x4e4f534a)+block+binary)
        if side.is_file():
            doc=json.loads(side.read_bytes());doc['bytes']=p.stat().st_size
            with p.open('rb')as stream:doc['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            side.write_text(json.dumps(doc,ensure_ascii=False,separators=(',',':'))+'\n')


def pigment(color,roughness=.84,metallic=0):
    v=np.array(color)/255.
    return dict(color=np.where(v<.04045,v/12.92,((v+.055)/1.055)**2.4).tolist(),roughness=roughness,metallic=metallic)


PALETTE={CAST:dict(color=[1.,1.,1.],texture=str(TEXTURE),roughness=.90),
        EDGE:pigment([173,172,159]),SHADE:pigment([100,103,102]),DRESS:pigment([154,151,139]),
        SOFFIT:pigment([119,119,110]),FLOOR:pigment([120,124,121]),INSET:pigment([137,136,125]),
        LETTER:pigment([209,209,198],.40,.29),METAL:pigment([67,71,70],.58,.24),
        PALE:pigment([117,154,175],.20,.16),MID:pigment([95,126,139],.23,.14),
        LOW:pigment([72,100,110],.24,.12),DARK:pigment([69,83,85],.36,.10)}

for name,alpha in GLASS_ALPHA.items():
    PALETTE[name]['alpha']=alpha


def ordinary(f,p,lod):
    lo=p['ordinary_sill'];pt=p['screen_pitch'];top=lo+12*pt;half=1.23*pt
    cuts=[]
    for x in (-p['pair_axis']/2,p['pair_axis']/2):
        cuts.append(box(x-half,lo,x+half,top))
        screen(f,x,lo,pt,12,True,lod)
    f.wall(lo,top,cuts,.58,CAST)
    regular_head(f,p,lod);terrace(f,p,lod)
    # On the rear the historic interior photograph shows four rings between
    # floor and ceiling. The section ends a short distance behind the window.
    for z in (lo,lo+4*pt,lo+8*pt,top):
        f.box(0,z-.098,f.length,.20,p['cut_depth']-.57,-(p['cut_depth']+.57)/2,FLOOR,'Inner floor edges')
    f.box(0,p['height_regular_parapet']-.15,f.length,.25,p['cut_depth']-.46,-(p['cut_depth']+.46)/2,SOFFIT,'Parapet slab')


def central(f,p,lod):
    lo=p['central_sill'];pt=p['central_pitch'];top=lo+13*pt;cuts=[]
    for side in (-1,1):
        x=side*p['centre_ring_separation']/2
        cuts.append(box(x-.505*pt,lo,x+.505*pt,top))
        # The raised central unit has narrow, single circular columns.
        screen(f,x,lo,pt,13,False,lod)
        sx=side*2.51;cuts.append(box(sx-.295,lo,sx+.295,top))
        side_louvres(f,sx,lo,top,lod)
    f.prism(box(-f.length/2,lo,f.length/2,top).difference(unary_union(cuts)),-.65,.18,CAST,'Solid entrance piers')
    centre_head(f,p,lod)
    for z in (lo,lo+4*pt,lo+8*pt,top):
        f.box(0,z-.11,f.length,.22,p['cut_depth']-.65,-(p['cut_depth']+.65)/2,FLOOR,'Entrance floor returns')
    f.box(0,p['height_entrance_cap']-.31,p['entrance_cap_width'],.25,p['cut_depth']-.58,-(p['cut_depth']+.58)/2,SOFFIT,'Central attic roof')


def end_faces(b,p,lod):
    half=p['facade_width']/2;depth=p['cut_depth'];z=p['height_regular_parapet']
    # Only the portions reaching the documented end pier are included. Both
    # attached side elevations continue beyond this independent facade section.
    for sign in (-1,1):
        y=sign*half
        if sign>0:end=Facade(b,[depth,y],[0.,y],'North end return')
        else:end=Facade(b,[0.,y],[depth,y],'South end return')
        end.wall(.08,z,(),.22,CAST)
        end.beam(z-.17,.19,.105,DRESS,label='End parapet band')


def add_building(b,lod):
    p=DIM;L=p['facade_width'];c=p['centre_bay'];pitch=(L-c)/8
    bounds=[-L/2+j*pitch for j in range(5)]+[c/2+j*pitch for j in range(5)]
    for j,(a,v) in enumerate(zip(bounds,bounds[1:])):
        is_centre=j==4;name='Central entrance' if is_centre else ('North bay '+str(4-j) if j<4 else 'South bay '+str(j-4))
        f=Facade(b,[0.,-a],[0.,-v],name)
        arcade(f,p,is_centre,lod)
        if is_centre:central(f,p,lod)
        else:ordinary(f,p,lod)
    for u in bounds:pier(b,u,p,abs(abs(u)-c/2)<.01,lod)
    end_faces(b,p,lod)
    # The measured west edge runs 0.95 degrees east of north.
    ang=-np.deg2rad(p['front_axis_bearing_deg'])
    rot=np.array([[np.cos(ang),-np.sin(ang)],[np.sin(ang),np.cos(ang)]])
    for part in b.parts:
        v=np.asarray(part['vertices']);v[:,:2]=v[:,:2]@rot.T
        part['vertices']=v.tolist()
    apply_metric_uv(b)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true')
    parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('unexpected raw export arguments: '+' '.join(rest))
        b=AggregateBuilder(PALETTE);add_building(b,args.lod);b.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['SLAUGHTERHOUSE_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
