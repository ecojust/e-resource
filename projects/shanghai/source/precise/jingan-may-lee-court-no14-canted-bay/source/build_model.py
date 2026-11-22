"""Build the photographed garden elevations of no. 14, May Lee Court."""
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
from garden_bay import PALETTE as BAY, add_building as add_bay, texture
from garden_main_corner import PALETTE as CORNER, add_garden_main_corner
from garden_quoin_drain import PALETTE as DRAIN, add_quoin_drain
from brick_return_uv import map_masonry_returns
from garden_extensions import PALETTE as EXT, add_extensions
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE

texture()
META=dict(id='jingan-may-lee-court-no14-canted-bay',name='美丽园14号园侧砖墙、折角钢窗与露台',
 viewer_page='may-lee-court-no14-canted-bay.html',heritage_group='5B005',
 scope='延安西路379弄14号园侧。包括两处两层外挑钢窗、露台铁栏、三层侧窗、转角隅石、落水管和照片中可见的折檐。尺度按署名照片估算。坡顶仅保留檐后可支撑的一段。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 attribution='园内原图93及弄外图71、76出自高参88，原文初刊于2014年并有后续增补。可下载模型使用原创几何与程序纹理。',copyright='Original garden frontage geometry and procedural brick texture, MIT.')
PALETTE={**BAY,**CORNER,**DRAIN,**EXT}

def add_building(builder,lod):
    add_bay(builder,lod,include_terrace_back=False)
    add_garden_main_corner(builder,lod)
    add_quoin_drain(builder,lod)
    add_extensions(builder,lod)
    map_masonry_returns(builder)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=AggregateBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['MAYLEE_GARDEN_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
