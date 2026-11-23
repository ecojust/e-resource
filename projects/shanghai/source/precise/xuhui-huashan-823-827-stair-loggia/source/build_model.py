"""Build the confirmed three-gabled street block at 823–827 Huashan Road."""
import argparse
import json
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
for path in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source',
             'xuhui-gaoan-77-curved-veranda/source']:
    sys.path.append(str(PROJECT/'source/precise'/path))
from crown_builder import CrownBuilder
from placement import Facade
from loggia_materials import PALETTE as LOGGIA
from wing_facades import add_wings, PALETTE as WINGS
from wing_finishes import REPEAT_METRES
from central_loggia import add_loggia

ID='xuhui-huashan-823-827-stair-loggia'
SLUG='huashan-823-827-stair-loggia'
SCALE=1.0
PALETTE={**LOGGIA,**WINGS}
META={'id':ID,'name':'华山路823、825、827号院临街住宅三山墙与明梯',
      'address':'上海市徐汇区华山路823、825、827号院','heritage_group':'5D051',
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'photo_source':'https://commons.wikimedia.org/wiki/File:华山路823号住宅.jpg',
      'photo_author':'Antigng','photo_reference_date':'2018-02-10','photo_reference_license':'CC BY-SA 4.0',
      'geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,
      'scope':'同一院门内可以辨认的临街住宅；现阶段包括中央拱厅及其中可见的一段明梯。'}


class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        vertices=[tuple(float(n)*SCALE for n in p) for p in vertices]
        super().add(vertices,faces,material,label)
        if material in REPEAT_METRES:
            sx,sz=REPEAT_METRES[material]
            obj=self.parts[-1]
            obj['texcoords']=[(u/(.78*sx),v/(.78*sz)) for u,v in obj['texcoords']]


def add_building(b,lod=False):
    add_loggia(Facade(b,label='Huashan Road | three-gabled street frontage'),lod)
    add_wings(b,lod=lod)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--lod',action='store_true')
    args=parser.parse_args();b=Builder(PALETTE);add_building(b,args.lod);print(b.save(args.output,META)['sha256'])
