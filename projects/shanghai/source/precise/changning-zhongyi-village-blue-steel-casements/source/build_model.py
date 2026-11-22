"""Photograph-based two-window section of the row houses at Lane 46, Jiangsu Road."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import numpy as np

SOURCE=Path(__file__).absolute().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as MetricBuilder
from photo_architecture import Facade
from brick_texture import CAST,TEXTURE,apply_metric_uv
from facing_brick import MORTAR,DARK,LIGHT,REVEAL,SILL,BED,add_facing
from steel_sashes import STEEL,BEAD,EDGE,IRON,BLUE,BLUE2,BLUE3,REFL,REFL2,GAP,window

META=dict(id='changning-zhongyi-village-blue-steel-casements',name='中一村江苏路46弄住宅青色钢窗与立砖窗楣',heritage_group='4M004',
          viewer_page='zhongyi-village-blue-steel-casements.html',scope='2018年原照中沿弄住宅二层的相邻两扇窗、两段立砖窗楣和其间的清水砖面。')
D=json.loads((SOURCE/'dimensions.json').read_bytes())
M=SOURCE.parent/'measurements'
BRICKS=json.loads((M/'brick-course-measurement.json').read_bytes())
LINTELS=json.loads((M/'soldier-joints.json').read_bytes())
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255;return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={CAST:dict(color=[1,1,1],roughness=.91,texture=str(TEXTURE)),MORTAR:pigment([191,173,164]),
         DARK:pigment([145,106,100]),LIGHT:pigment([169,129,119]),REVEAL:pigment([141,102,95]),
         SILL:pigment([157,162,155]),BED:pigment([104,101,98]),STEEL:pigment([73,96,86],.62,.22),
         BEAD:pigment([100,114,98]),EDGE:pigment([52,64,58]),IRON:pigment([66,68,63],.44,.6),
         BLUE:pigment([56,87,108],.39,.14),BLUE2:pigment([64,96,116],.39,.14),BLUE3:pigment([48,76,96],.41,.13),
         REFL:pigment([74,87,85],.32,.23),REFL2:pigment([67,80,79],.34,.24),GAP:pigment([46,52,55])}

class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')

def add_building(builder,lod):
    wall=Facade(builder,(-.5,0),(.5,0),'Lane wall')
    add_facing(builder,wall,D,BRICKS,LINTELS,lod)
    for idx,rect in enumerate([D['open_bay'],D['closed']]):window(builder,wall,rect,D,idx,lod)
    apply_metric_uv(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['ZHONGYI_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
