"""The photographed right-hand garden gable at 1518 Hongqiao Road."""
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



from garden_wall import CREAM, END, SASH, TIMBER, EDGE, GLASS, PLINTH, FIELD, gable
from oriel import CARVING, RELIEF_BASE, add_oriel
from returns import DRAIN, CUT, add_returns
from tiled_hip_roofs import ROOF_MATERIALS, add_roofs
from paint import TEXTURE, apply_metric_uv
META=dict(id='changning-hongqiao-1518-timber-gable-oriel',name='虹桥路1518号的木构山墙与三面凸窗',heritage_group='4M040',
          viewer_page='hongqiao-1518-timber-gable-oriel.html',scope='虹桥路1518号花园住宅南面右手的半歇山山墙、凸窗与底层弧窗。',
          photos_embedded=False,texture_license='MIT',geometry_license='MIT',source_period='2014年道路面与2018年花园面照片')
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)

PALETTE={**ROOF_MATERIALS, CREAM:dict(color=[1.,1.,1.],roughness=.94,texture=str(TEXTURE)),
         END:pigment([56,42,38]),SASH:pigment([66,45,37]),TIMBER:pigment([87,54,43]),
         EDGE:pigment([128,109,85]),PLINTH:pigment([229,219,194]),FIELD:pigment([210,198,171]),
         GLASS[0]:pigment([70,87,116],.34,.09),GLASS[1]:pigment([74,92,120],.34,.09),
         GLASS[2]:pigment([54,58,55],.35,.10),GLASS[3]:pigment([90,87,77],.36,.09),GLASS[4]:pigment([46,45,41],.35,.08),
         RELIEF_BASE:pigment([191,182,158]),CARVING:pigment([234,225,205]),DRAIN:pigment([74,70,62],.58,.13),
         CUT:pigment([196,187,162]),'Red brown roof cornice':pigment([101,62,49])}

class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')




def add_building(builder,lod):
    gable(builder,lod)
    add_oriel(builder)
    add_returns(builder,lod)
    add_roofs(builder,lod)
    apply_metric_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['HONGQIAO_1518_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
