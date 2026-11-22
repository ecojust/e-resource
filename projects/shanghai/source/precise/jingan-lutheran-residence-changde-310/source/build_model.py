"""Build the brick residence at 310 Changde Road."""
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
import paired_tower_windows, porch_columns, porch_end_piers, residence_fabric
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='jingan-lutheran-residence-changde-310',name='常德路310号信义会住宅的街面与庭院门廊',viewer_page='lutheran-residence-changde-310.html',heritage_group='5B021',
 scope='常德路310号临街砖塔、成对券窗、两侧坡屋与庭院入口。翼部进深、背坡及遮挡墙段采用摄影估形。',
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 attribution='灰砖、红券、石柱和雕饰据高参88、nina、CyberCop及独立街面照片量测。几何和两张重复纹理为原创。',
 copyright='Original architectural geometry, grey-brick and granite textures under the MIT license. Research photography remains with the credited photographers.')
PALETTE={**residence_fabric.PALETTE,**paired_tower_windows.PALETTE,**porch_columns.PALETTE,**porch_end_piers.PALETTE}
def add_building(builder,lod):
    residence_fabric.add_fabric(builder,lod)
    paired_tower_windows.add_tower_windows(builder,lod)
    porch_columns.add_porch(builder,lod,(-1.54,-.04,1.86),0.)
    # Blender stores object names in 63 UTF-8 bytes. Use the same full labels in each role.
    for part in builder.parts:
        label=part['label']
        for original,short in (('individual rectangular light','glass light'),('raised outer arch moulding','outer arch moulding'),('rolled intrados and reveal','rolled arch reveal'),('shallow inner arch under relief','inner segmental hood'),('Canted bay return | Canted return','Canted return |'),('scroll carving on the rounded bell','scrolls on bell')):
            label=label.replace(original,short)
        part['label']=label
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=RepeatingBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['CHANGDE_RESIDENCE_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=RepeatingBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
