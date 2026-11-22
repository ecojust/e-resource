"""Build the Continental Court apartment street corner."""
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
from repeat_materials import RepeatingBuilder
import continental_street_wall as wall
import continental_window_sashes as windows
import pointed_piers as piers
import street_shops_and_roof as shops
from finish_uv import metric_uv,map_return_faces
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='jingan-nanyang-continental-court-street-front',name='南洋大楼弧形街角、连续尖墩与陕西北路204号券门',viewer_page='nanyang-continental-court-street-front.html',heritage_group='5B041',
    scope='南京西路与陕西北路东南转角的四层南洋大楼。以十二根街面尖墩、十一开间、实拍204号通道、实测街区轮廓和平屋面构成；后院窗间与通道中段按已见边界估计。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
    attribution='高参88与高亦寒两组街面照片及现场铭牌；1941年《Shanghai Desk Hong List》第102、548页。数字纹理独立绘制。',
    copyright='Original reconstruction and procedural finishes licensed under MIT. Referenced photographs remain with their respective rights holders.')
PALETTE={**wall.PALETTE,**windows.PALETTE,**piers.PALETTE,**shops.PALETTE}
def add_building(builder,lod):
    wall.add_street_front(builder,lod)
    piers.add_pointed_piers(builder,lod)
    shops.add_shops_and_roof(builder,lod)
    for part in builder.parts:
        mat=part['material']
        if 'texture' in PALETTE[mat]:
            if 'texcoords' not in part:metric_uv(part,.54,.54)
            else:map_return_faces(part,.58)
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=RepeatingBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['NANYANG_CONTINENTAL_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=RepeatingBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
