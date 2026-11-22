"""Build the shared gatehouse at nos. 19 and 21 Yongjia Road."""
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

from gatehouse_fabric import PALETTE as SHELL, add_gatehouse_fabric
from gatehouse_upper_windows import PALETTE as WINDOWS, add_windows
from shared_lane_passage import PALETTE as PASSAGE, add_passage
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id="huangpu-xiai-hengai-common-lane-gate",name="永嘉路西爱村与恒爱里共用弄口",
 viewer_page="xiai-hengai-common-lane-gate.html",heritage_group="5A060",source_period="2015年街景、2017及2020年复核",
 scope="永嘉路19弄西爱村和21弄恒爱里共用门屋的街面、双层窗、内外过梁和有定位的入口区段。",
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 copyright="Original measured geometry and procedural grey render MIT. Replacement glyphs described in the font notice.",
 attribution="Original metric model of the shared Xiai Cun and Hengai Li gatehouse; no street photographs embedded.")
PALETTE={**SHELL,**WINDOWS,**PASSAGE,MATERIAL:dict(color=[1.,1.,1.],roughness=.95,texture=str(TEXTURE))}
def add_building(builder,lod):
    add_gatehouse_fabric(builder,lod)
    add_windows(builder,lod)
    add_passage(builder,lod)
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
        os.environ['YONGJIA_SHARED_GATE_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
