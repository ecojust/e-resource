"""Construct the five-bay Fuzhou Road facade of the former World Book Company."""
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
from material_names import MATERIAL,TEXTURE
from paint import apply_metric_uv

from shopfront import PALETTE as SHOP, add_carvings, add_shopfront, add_shop_mark, add_wall
from upper_bookshop_windows import PALETTE as WINDOWS, add_windows
from fuzhou_masonry import PALETTE as MASONRY, add_upper_masonry
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE

META=dict(id='huangpu-world-book-company-fuzhou-front',name='世界书局福州路立面与外文书店店面',
 viewer_page='world-book-company-fuzhou-front.html',heritage_group='5A048',source_period='2015年4月4日实照及2016年3月17日登记照片',
 scope='福州路390号临街立面，五开间五排上层窗，下部可见黑石檐、玻璃橱窗、入口与四尊石像。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright='Architectural reconstruction derived from Fayhoo, Waiwen Shudian, CC BY-SA 3.0. Original procedural Fuzhou brick texture MIT.',
 attribution='Fayhoo, Waiwen Shudian, 2015-04-04, Wikimedia Commons, CC BY-SA 3.0. The municipal-register photo essays of 2016 corroborate the observations.')
PALETTE={**SHOP,**WINDOWS,**MASONRY,MATERIAL:dict(color=[1.,1.,1.],roughness=.91,texture=str(TEXTURE))}
def add_building(builder,lod):
    add_wall(builder)
    add_shopfront(builder,lod)
    add_carvings(builder,lod)
    add_shop_mark(builder,lod)
    add_windows(builder,lod)
    add_upper_masonry(builder,lod)
    apply_metric_uv(builder)
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=AggregateBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['FUZHOU_BOOKSHOP_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
