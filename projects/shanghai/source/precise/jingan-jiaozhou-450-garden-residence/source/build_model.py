"""Build the registered Jiaozhou Road residence."""
import argparse
import os
from pathlib import Path
import sys

SOURCE=Path(__file__).absolute().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder
import garden_arcade,dormer,porch_back_wall,west_gable_and_roof
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE

garden_arcade.texture()
META=dict(id='jingan-jiaozhou-450-garden-residence',name='胶州路450号花园住宅的砖山墙、拱廊和老虎窗',viewer_page='jiaozhou-450-garden-residence.html',heritage_group='5B009',
 scope='胶州路450号住宅。庭院南面砖拱与瓶栏、廊后门窗、长老虎窗、西山墙及短返券据照片建模。第四拱远端、两段屋脊的接缝及北面按可见轮廓估形。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 attribution='区保护铭牌、上海静安与设计项目摄影、2020年2月街景作测量依据。公开模型使用原创几何与程序砖纹。',copyright='Original garden residence geometry and procedural running-bond texture, MIT.')
PALETTE={**garden_arcade.PALETTE,**dormer.PALETTE,**porch_back_wall.PALETTE,**west_gable_and_roof.PALETTE}
def add_building(builder,lod):
    garden_arcade.add_arcade(builder,lod)
    porch_back_wall.add_back_wall(builder,lod)
    dormer.add_dormer(builder,lod)
    west_gable_and_roof.add_fabric(builder,lod)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=AggregateBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['JIAOZHOU_GARDEN_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
