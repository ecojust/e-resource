"""Build the garden facade at Guanghuali No.13."""
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
import court_frontage, garden_gate_leaves, residential_facade, terrace_roof
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='jingan-guanghuali-no13-courtyard-front',name='光华里13号院门、三面凸窗与露台',viewer_page='guanghuali-no13-courtyard-front.html',heritage_group='5B025',
 scope='巨鹿路786弄13号院墙、灰窗套三面凸窗、右阔窗和露台。两期门牌实照辨明13号，后方与同排相接处按可见边界收口。',
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 attribution='高参88与言衣草的具名摄影提供院门和上层外观。模型几何、砖材和门牌字形为原创。',
 copyright='Original architectural mesh, ochre brick texture and drawn street lettering under the MIT license. Reference photographs remain with their respective photographers.')
PALETTE={**court_frontage.PALETTE,**garden_gate_leaves.PALETTE,**residential_facade.PALETTE,**terrace_roof.PALETTE}
def add_building(builder,lod):
    court_frontage.add_courtyard(builder,lod)
    garden_gate_leaves.add_gate_leaves(builder,lod)
    residential_facade.add_facade(builder,lod)
    place=residential_facade.PLACE
    terrace_roof.add_terrace(builder,lod,place['origin'],place['yaw_degrees'])
    for part in builder.parts:
        if part['material']==court_frontage.BRICK:residential_facade.brick_uv(part)
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=RepeatingBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['GUANGHUA_RESIDENCE_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=RepeatingBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
