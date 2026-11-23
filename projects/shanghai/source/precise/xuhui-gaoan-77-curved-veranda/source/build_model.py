"""Rebuild the garden exterior of the 1920s residence registered as 5D039."""
import argparse,json,os,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*HERE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))]if (p/'tools/package_architectural_model.py').is_file())
for directory in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source','xuhui-kangping-196-shuttered-residence/source']:
    sys.path.append(str(PROJECT/'source/precise'/directory))
from crown_builder import CrownBuilder as Builder
from placement import Facade
from materials import PALETTE
from east_return import add_east_return
from garden_front import add_front
from south_verandah import porch,dormer
from roof_and_returns import add_roof_and_returns
from west_wing import add_west_wing
ID='xuhui-gaoan-77-curved-veranda';SLUG='gaoan-77-curved-veranda'
META={'id':ID,'name':'高安路77号花园住宅折檐弧阳台','address':'上海市徐汇区高安路77号','heritage_group':'5D039','period':'1920年代','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html','photo_source':'https://commons.wikimedia.org/wiki/File:高安路77弄.JPG','viewer_page':SLUG+'.html','photo_author':'Antigng','photo_reference_date':'2013-03-08','photo_reference_license':'CC BY-SA 4.0','photo_reference_page':'https://commons.wikimedia.org/wiki/File:高安路77弄.JPG'}
META['camera_views']=json.loads((HERE/'cameras.json').read_text())
META['scope']='南面折檐弧阳台、三联窗、柱廊和老虎窗，西侧檐托、烟囱、门券及可辨屋顶；北面轮廓为近似收口。'
def add_building(b,lod=False):
    f=Facade(b)
    add_front(f,lod)
    porch(f,lod)
    dormer(f,lod)
    add_west_wing(f,lod)
    add_east_return(f,lod)
    add_roof_and_returns(f,lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);a.output.parent.mkdir(parents=True,exist_ok=True);r=b.save(a.output,META);print(r['parts'],r['triangles'],r['sha256'])
