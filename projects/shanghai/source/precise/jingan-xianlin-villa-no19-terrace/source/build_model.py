"""Build the courtyard elevations of Xianlin Villa No.19."""
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
import garden_terrace, courtyard_side_windows, residence_shell
from ochre_brick import make_texture
from asset_rights import licensed_writer,retain_metadata
from rights import PHOTO_AUTHOR,PHOTO_SOURCE,LICENSE_URL,GEOMETRY_LICENSE,TEXTURE_LICENSE
make_texture()
META=dict(id='jingan-xianlin-villa-no19-terrace',name='贤邻别墅愚园路470弄19号的转角露台与庭院立面',viewer_page='xianlin-villa-no19-terrace.html',heritage_group='5B013',
 scope='摄影者标注为19号的院内住宅。根据2015年原照片重建浅色长墙、转角小露台、黄砖露角和端面窗廊。背坡、树后墙段和底层被遮面积为收合估计。',
 geometry_license=GEOMETRY_LICENSE,texture_license=TEXTURE_LICENSE,photos_embedded=False,photo_author=PHOTO_AUTHOR,photo_source=PHOTO_SOURCE,license_url=LICENSE_URL,
 attribution='Fayhoo，Xianlin Bieshu.JPG，摄于2015年12月26日，CC BY-SA 3.0。模型、独立几何和程序砖纹为原创；含摄影原图的对照板保留原作者署名和许可。',copyright='Original geometry and procedural ochre brick texture, MIT. Source photograph by Fayhoo, CC BY-SA 3.0.')
PALETTE={**garden_terrace.PALETTE,**courtyard_side_windows.PALETTE,**residence_shell.PALETTE}
def add_building(builder,lod):
    residence_shell.add_fabric(builder,lod)
    courtyard_side_windows.add_windows(builder,lod)
    garden_terrace.add_terrace(builder,lod)

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--output',type=Path);parser.add_argument('--lod',action='store_true');parser.add_argument('--blender',default='blender')
    args,rest=parser.parse_known_args()
    if args.output:
        if rest:parser.error('Unknown raw mesh arguments')
        builder=AggregateBuilder(PALETTE);add_building(builder,args.lod);builder.save(args.output,META)
    else:
        if args.lod:parser.error('--lod requires --output')
        os.environ['XIANLIN_COURT_BLENDER']=args.blender
        sys.argv[1:]=[*rest,'--blender',str(SOURCE/'build_blender_source.py')]
        pack.Builder=AggregateBuilder;pack.retain_metadata=retain_metadata;pack.write_json=licensed_writer(pack.write_json,META)
        pack.build(SOURCE,META,PALETTE,add_building)
