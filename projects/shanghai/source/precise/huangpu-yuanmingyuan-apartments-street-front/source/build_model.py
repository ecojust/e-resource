"""Construct the east facade and the two corner loggias of Yuanmingyuan Apartments."""
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
from wing_casements import add_windows,PALETTE as WINDOWS
from central_brickwork import add_central_brickwork, PALETTE as CENTRAL
from english_name import add_english_name
from street_entrance import add_entrance,add_metal_letters,PALETTE as ENTRANCE
from east_facade import add_wings,add_side_loggias,add_recessed_entrance,PALETTE as WALL
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE

META=dict(id='huangpu-yuanmingyuan-apartments-street-front',name='圆明园公寓东立面与切角柱廊',
 viewer_page='yuanmingyuan-apartments-street-front.html',heritage_group='5A044',source_period='2014年1月27日实照，2016年3月、6月登记照片复核',
 scope='圆明园路115号沿街东立面和两侧可见切角，建模包括凹进门廊、十二组翼窗、中央砖券和两端柱廊。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright='Architectural reconstruction derived from Livelikerw, Yuanmingyuan Apartments Rockbund Shanghai, CC BY-SA 3.0. Original procedural brick texture MIT.',
 attribution='Livelikerw, Yuanmingyuan Apartments Rockbund Shanghai, 2014-01-27, Wikimedia Commons, CC BY-SA 3.0. The 2016 register photographs support independent measurements.')
PALETTE={**CENTRAL,**WALL,**ENTRANCE,**WINDOWS,MATERIAL:dict(color=[1.,1.,1.],roughness=.9,texture=str(TEXTURE))}
def add_building(builder,lod):
    add_entrance(builder,lod)
    add_recessed_entrance(builder,lod)
    add_metal_letters(builder)
    add_english_name(builder,lod)
    add_central_brickwork(builder,lod)
    add_wings(builder,lod)
    add_windows(builder,lod)
    add_side_loggias(builder,lod)
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
        os.environ['YUANMING_APARTMENTS_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
