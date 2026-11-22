"""Build the visible two-storey window wall of Huaya Hall."""
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
import pediment_windows as windows
import visible_wall_and_bay as walls
from finish_uv import metric_uv,map_return_faces
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='jingan-huaya-hall-jinde-school-window-pediments',name='花雅堂三联百叶窗、卷草山花与转角窗墙',viewer_page='huaya-hall-jinde-school-window-pediments.html',heritage_group='5B045',
    scope='延安中路718号花雅堂，按2016年两幅实照复原三联窗与相邻凸部的两层可见外墙。原照遮挡或未显示的范围以截面收口。三窗2.4米轴距为比例假定。',
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
    attribution='言衣草2016年11月2日实拍、上海市房屋管理局优秀历史建筑名录和静安区花雅堂介绍；公开几何与材质为原创。',
    copyright='Original reconstruction and procedural finishes licensed under MIT. Referenced photographs remain with their respective rights holders.')
PALETTE={**windows.PALETTE,**walls.PALETTE}
def add_building(builder,lod):
    windows.add_windows(builder,lod)
    walls.add_visible_walls(builder,lod)
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
        os.environ['HUAYA_HALL_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=RepeatingBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
