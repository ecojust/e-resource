"""Build the surveyed street frontage of the J.K.K. apartments."""
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

from jkk_street_fabric import PALETTE as FABRIC, add_street_fabric
from jkk_central_steel import PALETTE as CENTRAL, add_central_sashes
from jkk_balconies import PALETTE as BALCONIES, add_balconies
from asset_rights import licensed_writer, retain_metadata
from rights import PHOTO_AUTHOR, PHOTO_SOURCE, LICENSE_URL, GEOMETRY_LICENSE, TEXTURE_LICENSE

META = dict(id='jingan-jkk-apartments-changle-street-front', name='J.K.K.公寓长乐路临街立面与弧形阳台',
 viewer_page='jkk-apartments-changle-street-front.html',heritage_group='5B001',
 source_period='以2020年2月的街面为主，用2015年4月和12月的街景辨认受遮挡的构件。',
 scope='长乐路962弄1–4号登记街段，连续临街墙、两处楼梯窗、四列三层弧形阳台和照片可辨的挑檐。底窗被街墙遮挡处、屋顶进深和栋界均为估计。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright='Original measured architectural model and procedural mineral plaster texture, MIT.',
 attribution='Street observations from Baidu Maps, 2015 and 2020. The 1937, 1941 and 1942 Shanghai directories document the historical apartment name.')
PALETTE={**FABRIC, **CENTRAL, **BALCONIES, MATERIAL:dict(color=[1.,1.,1.],roughness=.91,texture=str(TEXTURE))}
def add_building(builder,lod):
    add_street_fabric(builder,lod)
    add_central_sashes(builder,lod)
    add_balconies(builder,lod)
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
        os.environ['CHANGLE_JKK_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
