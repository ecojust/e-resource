"""Build the open gate and courtyard facade of Lane 39 Yongjia Road."""
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

from courtyard_fabric import PALETTE as HOUSE
from courtyard_windows import PALETTE as WINDOWS
from courtyard_placement import add_courtyard
from entrance_ground import PALETTE as PAVING, add_entrance_ground
from zhengjia_gate import PALETTE as GATE, add_gate
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id="huangpu-zhengjia-lane-39-street-gate",name="永嘉路39弄郑家衖弄口与院内横屋",
 viewer_page="zhengjia-lane-39-street-gate.html",heritage_group="5A064",source_period="2015年街景与Antigng原照，2017–2020年复核",
 scope="永嘉路39弄临街双柱、铁门、弧形花池和街口铺地，以及从弄内可辨的三层横屋北立面、屋顶前坡及相连低翼的可见部分。两处实物相对方位与距离为影像估计。",
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright="Courtyard geometry derived from Antigng's 2015 photograph (CC BY-SA 4.0). Original procedural pebble-dash texture MIT. Replacement address glyphs SIL OFL 1.1.",
 attribution="Antigng photographed the courtyard on 9 September 2015. Identification follows the Yongjia Road street views and comparative features documented in the source.")
PALETTE={**HOUSE,**WINDOWS,**PAVING,**GATE,MATERIAL:dict(color=[1.,1.,1.],roughness=.95,texture=str(TEXTURE))}

def add_building(builder,lod):
    add_courtyard(builder,lod)
    add_entrance_ground(builder,lod)
    add_gate(builder,lod)
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
        os.environ['ZHENGJIA_LANE_39_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
