"""Build the museum’s registered south elevation and dated entrance from two 2014 views."""
import argparse,hashlib,json,os,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union

SOURCE=Path(__file__).absolute().parent
PROJECT=next((p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file()),None)
if PROJECT is None:
    PROJECT=Path(os.environ['E_RESOURCE_SHANGHAI'])
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model as pack
sys.path.insert(0,str(PROJECT/'source/precise/huangpu-somekh-building-street-corner/source'))
from aggregate_mesh import AggregateBuilder as TexturedBuilder


sys.path.insert(0,str(SOURCE))
from south_front import south_wall,roof,PALETTE as WALL
from portal_carvings import add_portal_carvings,PALETTE as RELIEF
from museum_sign import add_museum_sign,PALETTE as SIGN
from photo_plane import position
from material_names import MATERIAL
from paint import TEXTURE,apply_metric_uv
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
from asset_rights import licensed_writer,retain_metadata
META=dict(id='huangpu-puyutang-museum-south-front',name='普育堂旧址一号楼南立面与1925年门厅',
    heritage_group='5A032',viewer_page='puyutang-museum-south-front.html',source_period='2014年8月16日建筑档案照片',
    scope='普育西路105号一号楼南立面。包含红砖窗墙、可识别的双坡端部和门厅、石刻年份及馆名。',geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
    photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
    copyright='Original 3D geometry and procedural brick MIT. Replacement sign outlines from Noto Serif CJK SC, SIL OFL 1.1. No photographic pixels embedded.',
    attribution='Shanghai architectural heritage register, 16 August 2014 south elevation and entrance. Noto Serif CJK SC by Adobe and the Noto Project, SIL OFL 1.1.')
PALETTE={MATERIAL:dict(color=[1.,1.,1.],roughness=.96,texture=str(TEXTURE)),**WALL,**SIGN,**RELIEF}
def add_building(builder,lod):
    south_wall(builder)
    roof(builder,lod)
    add_portal_carvings(builder,lod,position,-.24,-.24)
    add_museum_sign(builder,lod,position,-.20)
    apply_metric_uv(builder)
AggregateBuilder=TexturedBuilder
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        scene=AggregateBuilder(PALETTE);add_building(scene,args.lod);scene.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['PUYUTANG_MUSEUM_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
