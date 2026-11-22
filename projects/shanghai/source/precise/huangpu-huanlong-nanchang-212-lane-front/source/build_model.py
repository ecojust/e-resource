"""Build two separately photographed entries at nos. 212 and 244 Nanchang Road."""
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

from upper_casements import PALETTE as WINDOWS,add_windows
from lane_212_fabric import PALETTE as FACADE,add_212_fabric
from iron_entrance import PALETTE as GATE,add_gate
from lane_244 import PALETTE as LANE244
from separate_entries import add_second_entry
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='huangpu-huanlong-nanchang-212-lane-front',name='南昌路212弄环龙别业门楼与244弄入口',
 viewer_page='huanlong-nanchang-212-lane-front.html',heritage_group='5A068',source_period='2015年署名照片与2015至2020年的入口影像',
 scope='南昌路212弄门柱、铁拱门与上方的外开窗、露台和过洞，以及约85.6米外244弄西侧绿牌、带窄窗的分缝墙和铁门一段。两处独立实物按摄影站推算的相对位置放置。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright="212 facade and entrance geometry derived from Antigng's 2015 photograph (CC BY-SA 4.0). Original procedural plaster texture MIT. Replacement address lettering SIL OFL 1.1.",
 attribution="Antigng photographed the numbered Nanchang Road Lane 212 entrance on 9 September 2015. The Lane 244 assembly uses separate dated observations, with no street-view imagery embedded.")
PALETTE={**WINDOWS,**FACADE,**GATE,**LANE244,MATERIAL:dict(color=[1.,1.,1.],roughness=.92,texture=str(TEXTURE))}
def add_building(builder,lod):
    add_212_fabric(builder,lod)
    add_windows(builder,lod)
    add_gate(builder,lod)
    add_second_entry(builder,lod)
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
        os.environ['HUANLONG_LANES_212_244_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
