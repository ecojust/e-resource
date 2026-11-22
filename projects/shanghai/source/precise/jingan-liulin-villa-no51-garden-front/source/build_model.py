"""Build the garden facade at Liulin Villa No.51."""
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
import court_gate, entrance_portal, garden_approach, liulin_loggia, residence_wings, terrace_parapet
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='jingan-liulin-villa-no51-garden-front',name='柳林别墅51号双凸窗、弧廊与花园门',viewer_page='liulin-villa-no51-garden-front.html',heritage_group='5B029',
 scope='愚园路532弄51号花园门、两翼三层凸窗、双层柱廊、退入的门窗、可见红瓦屋坡及院地。檐后屋面依可见轮廓截取。',
 photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
 attribution='高参88拍摄的花园外与庭院内两个角度可对应门牌、凸窗、柱廊和屋面。纹理与视图由本模型重新绘制。',
 copyright='Original architectural reconstruction, measured forms, lettering and procedural materials are licensed under MIT. Reference photographs are credited to their photographer.')
PALETTE={**residence_wings.PALETTE,**garden_approach.PALETTE,**court_gate.PALETTE,**liulin_loggia.PALETTE,**entrance_portal.PALETTE,**terrace_parapet.PALETTE}
def add_building(builder,lod):
    residence_wings.wings(builder,lod)
    liulin_loggia.add_loggia(builder,lod)
    terrace_parapet.add_parapet(builder,lod)
    entrance_portal.add_entrance(builder,lod)
    court_gate.add_court_gate(builder,lod)
    garden_approach.add_approach(builder,lod)
    scales={residence_wings.BRICK:(.92,.52),residence_wings.TILE:(.86,.72),garden_approach.PAVING:(.74,.74)}
    for part in builder.parts:
        if part['label'].startswith('Upper terrace | course '):
            part['label']=part['label'].replace('Terrace parapet | ', '')
        if part['material'] in scales:residence_wings.metric_uv(part,*scales[part['material']])
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=RepeatingBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['LIULIN_RESIDENCE_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=RepeatingBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
