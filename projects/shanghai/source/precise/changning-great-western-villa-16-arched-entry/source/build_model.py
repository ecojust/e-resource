"""Brick entrance, stair and embossed mailbox at No.16 Great Western Villa."""
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



from brick_entrance import STONES,MORTAR,PLUM,JOINT,WOOD,brickwork
from asset_rights import licensed_writer,retain_metadata
from letterbox import STONE,TEXTURE,EDGE,METAL,plaque_mesh,box_shelf
from stair_and_fittings import TREAD,RISER,BULL,RAIL,WALL,BOX,ZINC,stairs,hardware
META=dict(id='changning-great-western-villa-16-arched-entry',name='大西别墅16号的双重砖拱、花饰信报箱与楼梯',heritage_group='4M028',
          viewer_page='great-western-villa-16-arched-entry.html',scope='延安西路1453弄16号照片可见的门廊、入口两道拱、石饰信报箱与门后的十六级楼梯。')
META.update(copyright='Model and embedded photographic adaptations: CC BY-SA 4.0. Photograph by WQL, The mail box of No.16 Great Western Villa.jpg.',
            photos_embedded=True,photo_derivatives_embedded=True,geometry_license='CC BY-SA 4.0',texture_license='CC BY-SA 4.0',code_license='MIT',
            license_url='https://creativecommons.org/licenses/by-sa/4.0/',author_credit='建筑模型与几何编程由本项目制作；WQL的照片经透视校正并用于石面浮雕、金字和信箱铭牌。',
            attribution='WQL, The mail box of No.16 Great Western Villa.jpg, CC BY-SA 4.0. Photo rectified, cropped and adapted as relief. Model distributed under CC BY-SA 4.0.',
            attribution_url='https://commons.wikimedia.org/wiki/File:The_mail_box_of_No.16_Great_Western_Villa.jpg')
def pigment(rgb,rough=.82,metal=0):
    c=np.asarray(rgb)/255
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
primary={MORTAR:[185,166,148],PLUM:[135,83,72],JOINT:[164,140,125],WOOD:[138,63,56],TREAD:[111,98,84],RISER:[148,103,80],
         BULL:[154,142,121],RAIL:[149,68,66],WALL:[188,185,170],BOX:[64,61,60],ZINC:[144,145,140],METAL:[65,65,59],EDGE:[95,99,91],
         'Shaded salmon soffit':[154,96,85],'Muted brick soffit':[146,87,77],'Pale face mortar':[213,195,177],'Mortar on inner wall':[155,137,123],'Red frame shadow':[105,52,49],
         'Red faded door trim':[151,77,70],'Terracotta impost edge':[160,101,80],'Porch ceiling plaster':[178,173,163],'Warm grey threshold':[145,139,124],
         'Grey hall tile':[152,151,139],'Red turned newel cap':[161,67,63],'Red upper cupboard':[155,44,52],'Pale cabinet pull':[190,192,177],
         'Inner hallway in shade':[105,106,96],'Old oxblood door':[89,63,61],'Worn dark door panel':[93,67,62],'Stair beneath flight':[114,103,90],
         'Tile bed':[112,109,102],'Silver mailbox latch':[187,188,178],'Ivory label':[207,206,181],'Deep green enamel sign':[47,98,78],
         'Aged aluminium meter':[157,161,153],'Blue enamel meter':[77,116,145],'Grey meter window':[114,134,136],'Ochre service pipe':[164,140,79]}
for k,v in zip(STONES,[[177,117,100],[172,111,95],[181,120,101],[168,108,93]]):primary[k]=v
PALETTE={k:pigment(v,.55 if k in [WOOD,BOX,RAIL,METAL,EDGE]else .86,.21 if k in [METAL,ZINC,EDGE]else .0)for k,v in primary.items()}
PALETTE[STONE]=dict(color=[1,1,1],roughness=.75,texture=str(TEXTURE))
class AggregateBuilder(MetricBuilder):
    def save(self,path,metadata=None):
        super().save(path,metadata)
        p=Path(path);f=p.with_suffix('.geometry.json')
        if f.is_file():
            r=json.loads(f.read_bytes())
            with p.open('rb')as stream:r['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
            r['bytes']=p.stat().st_size;f.write_text(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')




def add_building(builder,lod):
    brickwork(builder,lod)
    stairs(builder,lod)
    hardware(builder,lod)
    plaque_mesh(builder,lod)
    box_shelf(builder,lod)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown options for a raw mesh')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['WESTERN16_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
