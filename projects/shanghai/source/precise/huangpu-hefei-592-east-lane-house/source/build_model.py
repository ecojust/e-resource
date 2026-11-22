"""Build the numbered entrance and east boundary gable at Lane 592, Hefei Road."""
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

from west_gable_fabric import PALETTE as WALL, add_west_gable
from lane_gate import PALETTE as GATE, add_lane_gate
from west_gable_shutters import PALETTE as WINDOWS, add_shutters
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id="huangpu-hefei-592-east-lane-house", name="合肥路592弄弄口与东侧山墙",
 viewer_page="hefei-592-east-lane-house.html",heritage_group="5A056",source_period="2015年2月街景及2017、2019年复核",
 scope="592弄门牌、两门柱和铁门，弄口东侧住宅的西山墙、三处百叶和邻接檐瓦。590和586号券廊另有门牌。",
 geometry_license=GEOMETRY_LICENSE, texture_license=TEXTURE_LICENSE, photos_embedded=False,
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright="Original measured geometry and procedural limewash MIT. Replacement address lettering from Noto CJK, SIL Open Font License 1.1.",
 attribution="Original geometry from numeric observations of Hefei Lane 592. No street-view pixels embedded. Address glyph font credit and OFL retained.")
PALETTE={**WALL,**GATE,**WINDOWS,MATERIAL:dict(color=[1.,1.,1.],roughness=.94,texture=str(TEXTURE))}
def add_building(builder,lod):
    add_west_gable(builder,lod)
    add_shutters(builder,lod)
    add_lane_gate(builder,lod)
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
        os.environ['HEFEI_LANE_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
