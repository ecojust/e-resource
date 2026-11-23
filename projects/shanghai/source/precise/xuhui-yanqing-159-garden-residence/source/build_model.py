"""Rebuild the garden entrance and street corner at 159 Yanqing Road."""
import argparse
import json
import os
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*HERE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))]
             if (p/'tools/package_architectural_model.py').is_file())
for folder in ('hongkou-general-post-office/source/common',
               'hongkou-tanggu-road-apartment-dated-crown/source',
               'xuhui-gaoan-77-curved-veranda/source'):
    sys.path.append(str(PROJECT/'source/precise'/folder))
from crown_builder import CrownBuilder
from placement import Facade
from corner_facades import entrance,street
from corner_attic import add_corner_attic,PALETTE as ATTIC
from north_roof import add_north_roof
from lower_gable import add_lower_gable, PALETTE as STAIR_ROOF
from court_layout import STREET_WINDOWS
from garden_finishes import REPEAT_METRES
from residence_materials import PALETTE as WALLS
from return_sashes import add_return_sash
from upper_sash import PALETTE as STEEL,add_upper_sash
ID='xuhui-yanqing-159-garden-residence'
SLUG='yanqing-159-garden-residence'
METRIC_SCALE=1.184
PALETTE={**WALLS,**STEEL,**ATTIC,**STAIR_ROOF}
META={'id':ID,'name':'延庆路159号住宅庭院拱门与临街转角','address':'上海市徐汇区延庆路159号',
      'heritage_group':'5D047','period':'建造年代待考，1934年行名录有该址公使馆记录',
      'geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'photo_source':'https://blog.sina.com.cn/s/blog_8001328c010305q4.html',
      'scope':'庭院拱门与相交的临街外墙、玻璃山墙、红瓦楼梯山墙及三管烟囱。未见室内与院后开窗待核。',
      'viewer_page':SLUG+'.html','camera_views':json.loads((HERE/'cameras.json').read_text())}


class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        # The scale comes from the independently triangulated axes of three street windows.
        metric=[tuple(float(x)*METRIC_SCALE for x in pt) for pt in vertices]
        super().add(metric,faces,material,label)
        if material in REPEAT_METRES:
            sx,sy=REPEAT_METRES[material]
            part=self.parts[-1]
            part['texcoords']=[(u/(.78*sx),v/(.78*sy)) for u,v in part['texcoords']]


def add_building(b,lod=False):
    garden=Facade(b,label='159 | garden entrance')
    along_street=Facade(b,along=(0,1),label='159 | street elevation')
    entrance(garden,lod)
    street(along_street,lod)
    add_upper_sash(b,lod=lod)
    add_corner_attic(b,lod=lod)
    add_north_roof(b,lod=lod)
    add_lower_gable(b,lod=lod)
    for name in ('near-open','attic-green','attic-pale'):
        add_return_sash(along_street,name,STREET_WINDOWS[name],lod=lod)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--lod',action='store_true')
    args=parser.parse_args()
    builder=Builder(PALETTE)
    add_building(builder,args.lod)
    result=builder.save(args.output,META)
    print(result['sha256'],result['triangles'])
