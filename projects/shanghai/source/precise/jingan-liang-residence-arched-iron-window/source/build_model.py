"""The 2012 iron window of Liang residence in Jingan."""
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



from window_wood import WOOD,DARK,INNER,GLASS,BRICK,PINK,CAP,RED,MORTAR,REFLECT,woodwork
from grille import FERRO,grille
from brick_surround import PALETTE as SURROUND,add_brick_surround
from rights import PHOTO_AUTHOR, PHOTO_SOURCE, LICENSE_URL
from redwood import MATERIAL,TEXTURE,metric_uv

META=dict(id='jingan-liang-residence-arched-iron-window',name='梁氏民宅的砖券铁花窗',heritage_group='4H005',
          viewer_page='liang-residence-arched-iron-window.html',scope='山西北路457弄61号具名院窗。上窗、下窗铁花、砖砌辐射眉拱与中央键砖、石窗台与砖裙。',
          photos_embedded=False,texture_license='MIT',geometry_license='CC BY-SA 3.0',source_period='2012年院内窗门原照，2015年山墙另照核址。',
          photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
          attribution='Window iron pattern traced from the photograph by Aaron Zhu, 4 July 2012, CC BY-SA 3.0.')
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
assert MATERIAL==WOOD
PALETTE={**SURROUND,WOOD:dict(color=[1.,1.,1.],roughness=.74,texture=str(TEXTURE)),
         DARK:pigment([78,48,40]),INNER:pigment([154,101,69]),GLASS[0]:pigment([65,60,54],.44,.15),
         GLASS[1]:pigment([59,62,61],.43,.13),BRICK:pigment([226,215,207]),PINK:pigment([222,205,197]),CAP:pigment([202,187,166]),RED:pigment([161,77,62]),
         MORTAR:pigment([201,188,173]),REFLECT:pigment([120,68,54]),FERRO:pigment([134,118,92],.59,.28)}

class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')




def add_building(builder,lod):
    woodwork(builder,lod)
    grille(builder,lod)
    add_brick_surround(builder,lod)
    metric_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['LIANG_GRILLE_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
