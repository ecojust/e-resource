"""Rebuild the garden exterior of the 1920s residence registered as 5D039."""
import argparse,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*HERE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))]if (p/'tools/package_architectural_model.py').is_file())
for directory in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source']:
    sys.path.append(str(PROJECT/'source/precise'/directory))
from crown_builder import CrownBuilder as Builder
from placement import Facade
from materials import PALETTE
from garden_front import add_front
ID='xuhui-gaoan-77-curved-veranda';SLUG='gaoan-77-curved-veranda'
META={'id':ID,'name':'高安路77号花园住宅折檐弧阳台','address':'上海市徐汇区高安路77号','heritage_group':'5D039','period':'1920年代','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html','photo_source':'https://commons.wikimedia.org/wiki/File:高安路77弄.JPG','viewer_page':SLUG+'.html','scope':'南面折檐木架、弧形阳台和窗组；建筑外观采用局部公制近似。'}
def add_building(b,lod=False):
    add_front(Facade(b),lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);a.output.parent.mkdir(parents=True,exist_ok=True);r=b.save(a.output,META);print(r['parts'],r['triangles'],r['sha256'])
