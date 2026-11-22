"""Build the measured north entrance of Maris Village on Wusheng Road."""
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


from gate_head import add_gate_surround, PALETTE as SURROUND
from gate_leaves import add_gate_leaves, PALETTE as LEAVES
from measured_medallions import add_medallions, PALETTE as MEDALLIONS
from material_names import MATERIAL
from paint import TEXTURE, apply_metric_uv
from asset_rights import licensed_writer, retain_metadata
from rights import PHOTO_AUTHOR, PHOTO_SOURCE, LICENSE_URL, GEOMETRY_LICENSE, TEXTURE_LICENSE

META=dict(id='huangpu-maris-village-wusheng-curved-gate',name='马立斯新村武胜路北门弧形铁架与四字门牌',
          heritage_group='5A020',viewer_page='maris-village-wusheng-curved-gate.html',
          scope='武胜路429弄北门的两道弧形铁架、重新小区四枚描金圆牌、双扇门与两侧一段墙栏。',
          source_period='2017至2021年武胜路街景',geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,
          photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
          copyright='MIT. Original editable geometry and procedural facing-brick texture. Survey sources remain with their provider.',
          attribution='Original mesh, numerical measurements and brick texture. The north gate of Lane 429, Wusheng Road, is documented in Baidu Maps street surveys of 2017, 2019, 2020 and 2021. Source photographs are referenced separately.')
PALETTE={MATERIAL:dict(color=[1.,1.,1.],roughness=.95,texture=str(TEXTURE)),**SURROUND,**LEAVES,**MEDALLIONS}
def add_building(builder,lod):
    add_gate_surround(builder,lod)
    add_gate_leaves(builder,lod)
    add_medallions(builder,lod)
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
        os.environ['MARIS_WUSHENG_GATE_BLENDER']=args.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder
        pack.retain_metadata=retain_metadata
        pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
