"""The projecting timbered gable and stone entry documented by the Changning district archive."""
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


from roughcast import CAST,TEXTURE,apply_metric_uv
from gable_frame import WOOD,WANE,CAP,ROOF,SOFFIT,STONE,BLACK,add_frame,add_verge
from entry_and_glazing import BRICKS,MORTAR,PLINTH,SHADOW_STONE,DOOR,RECESS,FRAME,GLASS,brick_field,door,sash

META=dict(id='changning-yuyuan-lane-865-timber-gable',name='愚园路865弄花园住宅木构图案山墙与内凹门洞',heritage_group='4M016',
    viewer_page='yuyuan-lane-865-timber-gable.html',scope='依长宁区五幢花园住宅资料中所配街景，重建一处可见的木构图案山墙、中央钢窗、砖墙和内凹门洞。该照片未注明五个门牌中的具体栋号。')

def pigment(rgb,rough=.87,metal=0):
    c=np.asarray(rgb)/255
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={CAST:dict(color=[1,1,1],texture=str(TEXTURE),roughness=.91),WOOD:pigment([52,45,42]),WANE:pigment([75,63,57]),
    CAP:pigment([116,130,140]),ROOF:pigment([102,100,99]),SOFFIT:pigment([161,146,124]),STONE:pigment([150,153,165]),
    BLACK:pigment([39,39,37]),MORTAR:pigment([169,139,131]),PLINTH:pigment([121,131,146]),SHADOW_STONE:pigment([108,108,118]),
    RECESS:pigment([55,48,47]),DOOR:pigment([60,51,50]),FRAME:pigment([58,62,60],.62,.17),
    'Deep glass reflection':pigment([52,59,65],.42,.20),'Faded brass':pigment([134,127,105],.56,.19),
    'Old switch box':pigment([158,154,142])}
for material,col in zip(BRICKS,[[145,84,78],[152,89,81],[141,80,75],[147,86,79],[137,78,74]]):PALETTE[material]=pigment(col)
for material,col in zip(GLASS,[[94,115,122],[93,100,102],[73,86,93],[103,125,135]]):PALETTE[material]=pigment(col,.41,.14)
class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')



def add_building(builder,lod):
    f=Facade(builder,(-.5,0),(.5,0),'Gabled front')
    brick_field(f,lod)
    door(f)
    aperture=add_frame(f,lod)
    sash(f,aperture,lod)
    add_verge(f,lod)
    apply_metric_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['YUYUAN865_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
