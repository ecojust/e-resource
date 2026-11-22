"""Street gable, three arched openings and pierced balcony of the Dai residence."""
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



from paint import TEXTURE,apply_metric_uv
from green_gable import GREEN,TRIM,CREAM,SASH,GLASS,TILES,gable,apron_details
from windows_and_balcony import ROUGH,RELIEF,BODY,LIP,SHADOW,lower_windows,balcony,pebble_finish

META=dict(id='changning-lixi-lane-24-dai-villa-gable',name='戴宅的绿色曲边山墙、三联拱窗与折角阳台',heritage_group='4M024',
          viewer_page='lixi-lane-24-dai-villa-gable.html',scope='利西路24弄5号沿街山墙与相接的一跨窗墙、花格阳台及可辨屋面局部。')
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={GREEN:dict(color=[1,1,1],roughness=.95,texture=str(TEXTURE)),TRIM:pigment([120,131,115]),CREAM:pigment([189,175,144]),
         SASH:pigment([49,79,66],.62),ROUGH:pigment([167,154,128]),RELIEF:pigment([194,174,142]),BODY:pigment([197,186,160]),
         LIP:pigment([216,204,176]),SHADOW:pigment([133,114,93]),'Pale drainpipe':pigment([200,196,175]),'Pipe collar':pigment([154,150,136]),
         'Faded attic sash':pigment([104,122,112]),'Attic apron in shade':pigment([162,153,137]),'Cream soffit':pigment([175,165,144]),
         'Sandy stone slab':pigment([156,144,125]),'Trough soil':pigment([83,76,60]),'Attic bracket in shade':pigment([71,79,64]),
         'Aggregate warm chip':pigment([175,155,120]),'Aggregate dark chip':pigment([129,119,96]),'Aggregate chalk chip':pigment([190,181,156])}
for k,v in zip(GLASS,[[69,80,81],[116,135,143],[77,96,104]]):PALETTE[k]=pigment(v,.38,.19)
for k,v in zip(TILES,[[176,101,67],[154,85,58],[188,125,86]]):PALETTE[k]=pigment(v,.88)

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
    apron_details(builder,lod)
    lower_windows(builder,lod)
    pebble_finish(builder,lod)
    balcony(builder,lod)
    apply_metric_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['DAI24_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
