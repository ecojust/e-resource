"""Build the former Daren School on Kangding East Road."""
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
import school_fabric, street_brick_arcade, triple_roof_gables
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='jingan-daren-school-kangding-20-street-front',name='康定东路20号原大任小学校沿街立面',viewer_page='daren-school-kangding-20-street-front.html',heritage_group='5B017',
 scope='康定东路20号临街长立面、三峰屋窗、十四孔券廊、钢窗长廊和外挑平台。院墙后的底层与背坡为轮廓估形。',
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 attribution='2015、2020年街面资料及街景写生达人2026年实景视频用于建筑测量。网格、逐楔券砖、瓦片和灰砖纹理为原创。',
 copyright='Original geometry and procedural grey brick texture, MIT. Photographs are referenced in the source measurements.')
PALETTE={**street_brick_arcade.PALETTE,**triple_roof_gables.PALETTE,**school_fabric.PALETTE}
def add_building(builder,lod):
    school_fabric.add_school(builder,lod)
    street_brick_arcade.add_brick_arcade(builder,lod)
    triple_roof_gables.add_gables(builder,lod)
    
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=AggregateBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['DAREN_SCHOOL_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
