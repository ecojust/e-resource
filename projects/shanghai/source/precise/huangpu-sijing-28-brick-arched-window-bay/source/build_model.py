"""Photographed two-storey east window bay at 28 Sijing Road, Shanghai."""
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


from east_wall import add_wall,MORTAR,RED,BURNT,BLUE,STONE,MOLD,REVEAL,DARK
from measured_arches import add_arches, PALETTE as ARCH_PALETTE
from casements import add_windows, PALETTE as WINDOW_PALETTE
from window_backing import add_window_backing, PALETTE as BACKING_PALETTE
from material_names import MATERIAL
from paint import TEXTURE,apply_metric_uv
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
META=dict(id='huangpu-sijing-28-brick-arched-window-bay',name='泗泾路28号住宅东端双层砖券窗与凹槽壁柱',heritage_group='5A016',
    viewer_page='sijing-28-brick-arched-window-bay.html',scope='以2017年街拍所见为界的东端两层券窗、蓝灰砖窗间墙、层间檐带和带凹槽的红砖壁柱。',
    source_period='Antigng摄于2017年8月31日',geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,
    photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
    copyright='Geometry CC BY-SA 4.0. Antigng, 31 August 2017. '+PHOTO_SOURCE+' . '+LICENSE_URL,
    attribution='Architecture and window details measured from Antigng’s 2017 photograph of 28 Sijing Road. Geometry CC BY-SA 4.0. Original brick grain and code MIT.')
def pigment(rgb,rough=.85,metal=0.):
    c=np.asarray(rgb)/255.
    return dict(color=np.where(c<.04045,c/12.92,((c+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={MATERIAL:dict(color=[1.,1.,1.],roughness=.97,texture=str(TEXTURE)),MORTAR:pigment([173,168,157]),RED:pigment([150,89,68]),BURNT:pigment([136,78,63]),BLUE:pigment([125,130,134]),STONE:pigment([186,179,159]),MOLD:pigment([140,78,58]),REVEAL:pigment([110,75,65]),DARK:pigment([45,45,43]),**ARCH_PALETTE,**WINDOW_PALETTE,**BACKING_PALETTE}
def add_building(builder,lod):
    add_wall(builder,lod)
    add_arches(builder,lod)
    add_windows(builder,lod)
    add_window_backing(builder,lod)
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
        os.environ['SIJING_EAST_BAY_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
