"""A section of the 1934 Hongqiao Sanatorium and its sunbathing terrace."""
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



from terraced_section import PLASTER,CONCRETE,TRIM,JOINT,METAL,SASH,GLASS,building
from checker_paving import TILES,TEXTURE,pavement
from tubular_chairs import TUBE,FABRIC,SEAM,chairs
from terrace_planting import POT,RIM,SOIL,BARK,FOLIAGE,planting
META=dict(id='changning-hongqiao-sanatorium-sun-terraces',name='虹桥疗养院的四层退台、方格晒台与弯管躺椅',heritage_group='4M036',
          viewer_page='hongqiao-sanatorium-sun-terraces.html',scope='1934年前后历史主楼南侧两跨局部、四层退台与照片可见的顶层晒台。',
          photos_embedded=False,texture_license='MIT',geometry_license='MIT',source_period='约1934年，老伊犁路2号')
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={PLASTER:pigment([211,210,199]),CONCRETE:pigment([180,178,164]),TRIM:pigment([221,219,205]),JOINT:pigment([119,118,110]),
         METAL:pigment([200,202,191],.48,.12),SASH:pigment([102,104,99],.57,.12),GLASS:pigment([129,137,137],.37,.2),
         'Grey stone sill':pigment([168,169,160]),'Exposed cement paving':pigment([168,163,149]),'Rear wall in section':pigment([178,177,165]),
         'Post plinth shadow':pigment([138,137,125]),'End wall in shade':pigment([149,148,137]),'Charcoal parapet plinth':pigment([101,102,97]),
         TUBE:pigment([169,176,171],.32,.38),FABRIC:pigment([199,191,163],.96),SEAM:pigment([166,160,142],.9),
         POT:pigment([92,87,76]),RIM:pigment([112,104,89]),SOIL:pigment([65,63,55]),BARK:pigment([100,99,78]),
         FOLIAGE[0]:pigment([74,86,72]),FOLIAGE[1]:pigment([64,76,63]),FOLIAGE[2]:pigment([81,92,79]),
         TILES:dict(color=[1.,1.,1.],roughness=.77,texture=str(TEXTURE))}

class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')




def add_building(builder,lod):
    building(builder,lod)
    pavement(builder,lod)
    chairs(builder,lod)
    planting(builder,lod)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['HONGQIAO_SANATORIUM_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
