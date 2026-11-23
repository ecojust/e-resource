"""Rebuild the photographically registered garden elevation of the former residence."""
import argparse,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*HERE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))] if (p/'tools/package_architectural_model.py').is_file())
for path in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source']:
    sys.path.append(str(PROJECT/'source/precise'/path))
from crown_builder import CrownBuilder as Builder
from materials import PALETTE as MATERIALS
from arch_brick_and_glass import PALETTE as ORNAMENT,layout_from_photo
from garden_plane import SURVEY,hit
from placement import Facade
from garden_front import add_garden_front
from garden_letters import add_letters
PALETTE=MATERIALS|ORNAMENT
ID='xuhui-jianguo-629-rounded-garden-residence';SLUG='jianguo-629-rounded-garden-residence'
META={'id':ID,'name':'建国西路629号住宅花园立面','address':'上海市徐汇区建国西路629号','heritage_group':'5D027','period':'老住宅的花园立面，以2017年照片和2019年刊载的照片配准','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html','photo_source':'https://commons.wikimedia.org/wiki/File:建国西路629弄.jpg','viewer_page':SLUG+'.html','scope':'可见花园立面和圆转角。局部公制尺寸由砖的皮数估算，建筑地理朝向和遮挡区屋深待考。'}
def add_building(b,lod=False):
    layout=layout_from_photo(hit,storey_height=SURVEY['storey_m'])
    face=Facade(b)
    add_garden_front(face,layout,lod)
    add_letters(face,lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);a.output.parent.mkdir(parents=True,exist_ok=True);r=b.save(a.output,META);print(r['parts'],r['triangles'],r['sha256'])
