"""The courtyard elevation of Qixia Village, Nos 6–9, Lane 372 Wuyuan Road."""
import argparse,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
from no6_loggia import PALETTE as SIX,add_no6_loggia
from no7_enclosure import PALETTE as SEVEN,add_no7_enclosure
from no9_court import PALETTE as NINE,add_no9_court
from court_masonry import PALETTE as MASON,architecture,Camera,F67,F9,BACK,WALL,slab,height
from courtyard_wall import COURT,add_boundary
ID='xuhui-qixia-village-wuyuan-372';SLUG='qixia-village-wuyuan-372'
PALETTE={**MASON,**SIX,**SEVEN,**NINE}
META={'id':ID,'name':'栖霞村6–9号院向立面','address':'上海市徐汇区五原路372弄6–9号','heritage_group':'5D071',
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'photo_source':'https://4travel.jp/travelogue/11103136','photographer':'中国の風景','photo_author':'中国の風景','photo_date':'2016-01-20','photographic_date':'2016-01-20',
      'geometry_license':'MIT','texture_license':'MIT','photos_embedded':False,'viewer_page':SLUG+'.html',
      'scope':'西北一排朝院可辨的街屋、门柱和阳台。6、7、9号有独立题名，间跨窗组尚未确定为8号单户。'}
if (HERE/'cameras.json').is_file():
    META['camera_views']=json.loads((HERE/'cameras.json').read_text())

def add_building(b,lod=False):
    ends=architecture(b,lod)
    add_no6_loggia(b,Camera(17),F67,BACK,lod)
    add_no7_enclosure(b,Camera(18),F67,BACK,lod)
    open_sections=add_no9_court(b,Camera(20),F9,BACK,lod,court_y=COURT)
    for level,data in open_sections.items():
        slab(b,data['divide_left'],data['divide_right'],F9,BACK,data['top'],
             height(data['divide_left']) if level=='upper' else open_sections['upper']['underside'],
             WALL,'No 9 open terrace | cream partition between the decks')
    add_boundary(b,ends,lod)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod);print(b.save(a.output,META)['sha256'])
