"""Build the documented Xinlefang street-corner entrance and service-pipe bay."""
import argparse
import json
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(HERE),str(HERE.parent/'measurements'),
               str(PROJECT/'source/precise/hongkou-general-post-office/source/common'),
               str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source')]
from photo_architecture import Builder as GeometryBuilder
from crown_builder import CrownBuilder
import street_portal
import service_flues
import facing
import street_masonry
import shop_signs
import front_windows
import lane_return
import roof_edge
import front_shops

ID='xuhui-xinle-143-1-street-corner'
SLUG='xinle-143-1-street-corner'
PALETTE=street_portal.PALETTE|service_flues.PALETTE|street_masonry.PALETTE|facing.PALETTE|shop_signs.PALETTE|front_windows.PALETTE|lane_return.PALETTE|roof_edge.PALETTE|front_shops.PALETTE
META={'id':ID,'name':'新乐坊143-1号临街窗墙与弄口门柱','address':'上海市徐汇区新乐路143弄1–4号，新乐路143-1临街前楼',
      'heritage_id':'sh-historic-b5-xh-j-107-v','heritage_group':'5D107',
      'source':'https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html',
      'photo_source':'https://commons.wikimedia.org/wiki/Special:Redirect/page/66206083',
      'photo_author':'Antigng, 2018-02-07, CC BY-SA 4.0','photos_embedded':False,
      'camera_views':json.loads((HERE/'cameras.json').read_bytes()),
      'geometry_license':'CC BY-SA 4.0','texture_license':'CC BY-SA 4.0','viewer_page':SLUG+'.html',
      'local_axes':'Street facade datum at 143-1. X increases right in the 2018 photograph, Y is inward and Z is up.',
      'scope':'143-1门面与临街转角实照可见的两块号码牌、双扇门、两处店招、七樘钢窗和两支金属穿墙管，东段底层店面、绿门和表箱，以及弄内7.1米可见窗墙、檐槽和水斗。'}

class Builder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        before=len(self.parts)
        super().add(vertices,faces,material,label)
        if len(self.parts)>before and material in facing.STEMS:facing.set_metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        GeometryBuilder.save(self,path,metadata)
        return facing.finish_materials(path,self.palette)

def add_building(b,lod=False):
    street_masonry.add_street_masonry(b,-8.719,2.387,[street_portal.door_opening(),*front_windows.front_openings(),*front_shops.front_openings()],lod)
    street_portal.add_portal(b,lod)
    service_flues.add_flues(b,lod)
    shop_signs.add_shop_signs(b)
    front_windows.add_front_windows(b,lod)
    lane_return.add_lane_return(b,lod)
    roof_edge.add_roof_edge(b,lod)
    front_shops.add_front_shops(b,lod)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    a=p.parse_args();b=Builder(PALETTE);add_building(b,a.lod)
    print(b.save(a.output,META)['sha256'])
