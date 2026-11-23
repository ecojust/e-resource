"""Export the surveyed street section of 364 South Xiangyang Road in metres."""
from pathlib import Path
import argparse
import json
import os
import sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*HERE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))] if (p/'tools/package_architectural_model.py').is_file())
for path in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source']:
    sys.path.append(str(PROJECT/'source/precise'/path))
from crown_builder import CrownBuilder as Builder
from materials import PALETTE as SURFACES
from numbered_entrance import PALETTE as ENTRANCE
from placement import Facade
from street_body import add_body
PALETTE=SURFACES|ENTRANCE
ID='xuhui-xiangyang-364-arched-residence'
SLUG='xiangyang-364-arched-residence'
META={'id':ID,'name':'襄阳南路364号住宅','address':'上海市徐汇区襄阳南路364号','heritage_group':'5D023','period':'上海市第五批优秀历史建筑。公开观察记录为2015、2018和2020年。','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html','photo_source':'https://mapsv0.bdimg.com/?qt=sdata&sid=09000300122002221452176135O','camera_views':json.loads((HERE/'cameras.json').read_bytes()),'viewer_page':SLUG+'.html','scope':'沿街三层及顶部小屋可见截段；正面、南圆转角、北侧单排上下两窗。内界按街面西侧3.18米截取。'}
def add_building(b,lod=False):
    front=Facade(b,along=(.0185,.99983))
    add_body(front,lod)
    from roof_room import add_roof_room
    add_roof_room(front,lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--lod',action='store_true')
    a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    report=b.save(a.output,META)
    print(report['triangles'],report['parts'],report['sha256'])
