"""Rounded upper storeys at no. 65, Lane 749 Yuyuan Road, Shanghai."""
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


from aggregate_finish import CAST,TEXTURE,apply_metric_uv
from rounded_wall import wall,dressings,COAT,SOOT,MORTAR,BRICKS,JOINT
from steel_windows import STEEL,SILL,SHADOW,BLUES,LEFT,RIGHT,METAL,LEAD,PALE,GREY,windows,wall_equipment

META=dict(id='changning-yuyuan-lane-749-curved-front',name='2018年署名「愚园路749弄65号」照片中的灰色弧面住宅',heritage_group='4M012',
          viewer_page='yuyuan-lane-749-curved-front.html',identification_state='photograph_link_only',scope='按2018年同名署名照片重建灰色圆弧转角的三个开间、六樘窗和竖向嵌砖。区级65号档案照片另见红砖弧面，两立面的楼栋关系待核。')
D=json.loads((SOURCE/'dimensions.json').read_bytes());M=SOURCE.parent/'measurements'
PIER=json.loads((M/'vertical-brick-pier.json').read_bytes());SWING=json.loads((M/'lower-casement-fit.json').read_bytes())
def pigment(rgb,rough=.85,metal=0):
    c=np.asarray(rgb)/255;return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={CAST:dict(color=[1,1,1],texture=str(TEXTURE),roughness=.90),COAT:pigment([122,114,110]),SOOT:pigment([78,76,76]),
    MORTAR:pigment([156,147,140]),BRICKS[0]:pigment([93,74,65]),BRICKS[1]:pigment([77,66,65]),BRICKS[2]:pigment([86,69,70]),
    BRICKS[3]:pigment([121,90,70]),JOINT:pigment([75,76,74]),'Fired lower brick edge':pigment([111,87,75]),'Coping lower drip':pigment([99,92,88]),
    STEEL:pigment([53,61,63],.58,.24),SILL:pigment([102,100,90]),SHADOW:pigment([49,52,51]),
    BLUES[0]:pigment([95,131,161],.4,.16),BLUES[1]:pigment([129,153,176],.41,.14),BLUES[2]:pigment([88,117,147],.39,.18),
    LEFT[0]:pigment([125,119,117],.42,.11),LEFT[1]:pigment([139,126,120],.44,.12),RIGHT[0]:pigment([158,180,189],.41,.16),
    'Pale reflected lintel':pigment([166,182,193],.4,.14),METAL:pigment([156,148,119],.54,.28),LEAD:pigment([136,161,168],.47,.10),
    PALE:pigment([174,200,208],.36,.20),GREY:pigment([82,99,106],.4,.2),'Shaded reflection bar':pigment([69,76,80]),
    'Brown steel':pigment([89,70,65],.58,.18),'Oxide curtain':pigment([105,82,76]),'Pale backing cloth':pigment([156,149,130]),
    'Cool grey glass':pigment([128,148,151],.43,.13),'Pale condenser enamel':pigment([190,187,169]),'Dusty condenser grille':pigment([121,126,118]),
    'Faded condenser rib':pigment([171,172,158]),'Ivory insulation':pigment([174,169,146])}
class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')



def add_building(builder,lod):
    wall(builder,D,lod)
    dressings(builder,D,PIER,lod)
    windows(builder,D,SWING,lod)
    wall_equipment(builder,D,lod)
    apply_metric_uv(builder,D['radius_m'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['YUYUAN749_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.build(SOURCE,META,PALETTE,add_building)
