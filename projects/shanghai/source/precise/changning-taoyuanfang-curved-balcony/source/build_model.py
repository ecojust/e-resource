"""The bow-fronted end balcony at Taoyuan Fang seen in Antigng's February 2018 photograph."""
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
from slab_and_cheeks import CAST,EDGE,LINE,SOFFIT,REAR,RED,MORTAR,CHEEK,SASH,GLASS,floor,cheeks,pendant
from wrought_guard import IRON,WORN,TIP,draw_guard
from drying_rack import STEEL,DARK,LITE,PIN,END,hardware

META=dict(id='changning-taoyuanfang-curved-balcony',name='桃源坊端部阳台的折弧线脚、卷草铁栏与四杆晾衣架',heritage_group='4M020',
          viewer_page='taoyuanfang-curved-balcony.html',scope='依2018年有署名的桃源坊照片，重建一跨端部阳台、栏板、可折晾衣架、短段相接窗墙与灯具。照片未注明具体门牌。')

def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255;return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={CAST:dict(color=[1,1,1],texture=str(TEXTURE),roughness=.91),EDGE:pigment([187,192,186]),LINE:pigment([133,145,143]),
    SOFFIT:pigment([175,162,136]),REAR:pigment([203,191,170]),RED:pigment([151,93,77]),MORTAR:pigment([201,174,148]),
    CHEEK:pigment([130,143,135]),SASH:pigment([63,66,63],.53,.17),IRON:pigment([48,47,44],.60,.22),WORN:pigment([79,76,69],.64,.13),
    TIP:pigment([67,63,55],.57,.22),STEEL:pigment([184,189,184],.28,.64),DARK:pigment([72,69,63],.52,.3),
    LITE:pigment([141,141,128],.46,.35),PIN:pigment([179,163,111],.48,.19),END:pigment([160,161,152],.64,.08),
    'Clamp cast steel':pigment([146,145,136],.55,.27),'Deep recess':pigment([46,43,42]),'Shaded rear pane':pigment([66,66,63],.42,.16),
    'Lamp enamel':pigment([64,62,51],.53,.20),'Pale light bulb':pigment([183,179,152],.45,.13)}
for k,c in zip(GLASS,[[134,153,163],[159,173,175],[114,129,140]]):PALETTE[k]=pigment(c,.39,.17)
class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')




def add_building(builder,lod):
    floor(builder,lod)
    cheeks(builder,lod)
    draw_guard(builder,lod)
    hardware(builder,lod)
    pendant(builder,lod)
    apply_metric_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['TAOYUAN1292_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
