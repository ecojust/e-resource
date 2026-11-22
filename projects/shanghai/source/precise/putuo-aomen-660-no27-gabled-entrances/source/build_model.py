"""The garden gable above the house at No. 27, Lane 660 Aomen Road."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

SOURCE=Path(__file__).absolute().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:
    PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as TexturedBuilder
from garden_gable import add_gable,rect,poly,x,z,FIELD,WOOD,LINTEL,IRON,SUPPORT,GLASS,TIMBER,PORTLAND,PLINTH,BRICKS
from clipped_roof import add_roof,TILES,FASCIA,CAP,MORTAR
from wall_section import add_section,CUT,FOUNDATION
from paint import TEXTURE,apply_metric_uv
META=dict(id='putuo-aomen-660-no27-gabled-entrances',name='澳门路660弄27号山墙下的双门廊',heritage_group='4N002',viewer_page='aomen-660-no27-gabled-entrances.html',scope='澳门路660弄27号门牌旁的两座门廊、上层木窗与挑栏、截头山墙和屋顶前段。',source_period='2015年3月带门牌的现场照片。',geometry_license='MIT',texture_license='MIT',photos_embedded=False)
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255.
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
SURFACES={WOOD:(57,60,54),LINTEL:(212,209,193),IRON:(97,63,56),SUPPORT:(124,112,96),TIMBER:(82,66,59),PORTLAND:(173,148,114),PLINTH:(161,129,110),FASCIA:(129,87,77),CAP:(173,169,158),MORTAR:(86,77,70),CUT:(155,140,120),FOUNDATION:(143,136,122)}
SURFACES.update(zip(BRICKS,[(162,108,85),(174,116,92),(167,111,92)]))
SURFACES.update(zip(TILES,[(137,102,84),(105,87,78),(126,89,77),(145,105,88)]))
PALETTE={k:pigment(rgb) for k,rgb in SURFACES.items()}
PALETTE.update({k:pigment(rgb,.41,.12) for k,rgb in zip(GLASS,[(94,99,94),(80,89,77),(81,89,93)])})
PALETTE[FIELD]=dict(color=[1.,1.,1.],roughness=.93,texture=str(TEXTURE))
from paired_entries import PALETTE as ENTRY_PALETTE,add_entries
PALETTE.update(ENTRY_PALETTE)
def opening(cx,base,rx,rz,slope):
    pts=[]
    for a in np.linspace(0.,np.pi,49):
        u=cx+rx*np.cos(a);v=base-rz*np.sin(a)+slope*(u-cx)
        pts.append((u,v))
    return poly(pts)
def add_building(builder,lod):
    holes=[rect(165,252,232,359),rect(299,249,373,359),
           opening(198.2531,241,29.57,31.49,-.025),opening(332.4871,237.8,33.22,33.37,-.036)]
    add_gable(builder,lod,holes);add_entries(builder,lod);add_roof(builder,lod);add_section(builder);apply_metric_uv(builder)
class AggregateBuilder(TexturedBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);side=p.with_suffix('.geometry.json')
        if side.is_file():
            record=json.loads(side.read_bytes())
            with p.open('rb') as file:record['sha256']=hashlib.file_digest(file,'sha256').hexdigest()
            record['bytes']=p.stat().st_size;side.write_text(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['AOMEN_27_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
