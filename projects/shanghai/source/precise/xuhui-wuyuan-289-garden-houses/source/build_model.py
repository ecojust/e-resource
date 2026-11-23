"""Build the independently addressed Maresca maisonettes from their registered sources."""
from pathlib import Path
import argparse,json,sys,os
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in [*HERE.parents,Path(os.getenv('E_RESOURCE_SHANGHAI','.'))]if (p/'tools/package_architectural_model.py').is_file())
for sub in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source']:
    sys.path.insert(0,str(PROJECT/'source/precise'/sub))
from crown_builder import CrownBuilder as Builder
from materials import PALETTE as HOUSE_PALETTE
from lane_gate import PALETTE as GATE_PALETTE
PALETTE=HOUSE_PALETTE|GATE_PALETTE
from placement import Facade
from northern_front import add_one_two
from body import add_body
import house_three_openings as south_front
from grounds import add_lane
ID='xuhui-wuyuan-289-garden-houses'
SLUG='wuyuan-289-garden-houses'
META={'id':ID,'name':'五原路289弄花园住宅','address':'上海市徐汇区五原路289弄1–2、3–4号','heritage_group':'5D019','period':'1930年代英式联立住宅，按1935年相册、2013年门牌近照和四期影像重建','geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'source':'https://m.thepaper.cn/baijiahao_16359621','photo_source':'https://brs.russianshanghai.city/architects/a-l/v-n-dronnikoff','camera_views':json.loads((HERE/'cameras.json').read_bytes()),'viewer_page':SLUG+'.html'}
def add_north(b,lod=False):
    north=Facade(b,'1-2')
    add_body(north,lod)
    add_one_two(north,lod)
def add_building(b,lod=False):
    add_north(b,lod)
    south=Facade(b,'3-4')
    add_body(south,lod,(south_front.BIG,south_front.SMALL))
    south_front.add_three_four(south,lod)
    add_lane(b,lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true');a=p.parse_args()
    b=Builder(PALETTE);add_building(b,a.lod);a.output.parent.mkdir(exist_ok=True,parents=True);r=b.save(a.output,META)
    print(r['triangles'],r['parts'],r['sha256'])
