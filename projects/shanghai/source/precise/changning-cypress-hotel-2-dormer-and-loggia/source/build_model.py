"""A lawn-facing section of Cypress Hotel Villa 2."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import box

SOURCE=Path(__file__).absolute().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as MetricBuilder
from photo_architecture import Facade



from cypress_brick_windows import PALETTE as BRICK, add_brick_front
from cypress_dormer import WOOD,DARK,TRIM,FIRED,GLASS_LEFT,GLASS_RIGHT,CURTAIN,EDGE,BEAD,add_dormer
from cypress_roof import CLAY,PALE,RED,JOINT,RIDGE,add_roof,apply_roof_uv
from clay_finish import MATERIAL,TEXTURE
from cut_surfaces import SHADE,TOP,add_cuts
from porch_roof import add_porch_roof
from cypress_loggia import PALETTE as PORCH, add_loggia
META=dict(id='changning-cypress-hotel-2-dormer-and-loggia',name='龙柏饭店2号楼的双扇老虎窗与草坪柱廊',heritage_group='4M044',
          viewer_page='cypress-hotel-2-dormer-and-loggia.html',scope='虹桥路2419号龙柏2号楼草坪面中段与右侧双孔柱廊，仅取原照片可辨的建筑局部。',
          photos_embedded=False,texture_license='MIT',geometry_license='MIT',source_period='1930年代，上海泰晤士报报社')
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
assert MATERIAL==CLAY
PALETTE={**BRICK,**PORCH,SHADE:pigment([92,68,54]),TOP:pigment([145,132,111]),CLAY:dict(color=[1.,1.,1.],roughness=.88,texture=str(TEXTURE)),
         PALE:pigment([208,147,89]),RED:pigment([181,112,68]),JOINT:pigment([108,68,43]),RIDGE:pigment([194,117,66]),
         WOOD:pigment([133,61,44]),DARK:pigment([79,49,43]),TRIM:pigment([169,89,57]),FIRED:pigment([203,146,91]),
         GLASS_LEFT:pigment([107,116,134],.40,.11),GLASS_RIGHT:pigment([72,77,90],.39,.10),CURTAIN:pigment([213,203,174]),
         EDGE:pigment([89,66,51],.68,.12),BEAD:pigment([173,111,81])}

class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')




def add_building(builder,lod):
    add_brick_front(builder,lod)
    add_loggia(builder,lod)
    add_roof(builder,lod)
    add_porch_roof(builder,lod)
    add_dormer(builder,lod)
    add_cuts(builder)
    apply_roof_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['CYPRESS_TWO_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
