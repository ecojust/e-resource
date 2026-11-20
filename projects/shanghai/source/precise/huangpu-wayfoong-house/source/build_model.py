"""Deliver the west-facing former HSBC staff housing on Middle Sichuan Road."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from wayfoong_geometry import PALETTE,make_house

ID='huangpu-wayfoong-house'
SCOPE='四川中路210–220号双号、1928年新汇丰大楼职员宿舍，含西面五组三联窗、两翼双门和上层阁楼，后部采光井及附属屋面按航片概化。'
META={'id':ID,'name':'新汇丰大楼（汇丰银行职员宿舍）','status':'original-photo-informed-exterior',
      'scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'wayfoong-house.html',
      'estimated':'单体外轮廓据具名城市源，层高、门窗进深、凸饰、顶层、天井与东侧隐面高度按照片与航片估计。',
      'coordinate_convention':'Local GLB +X runs south along Middle Sichuan Road, +Y is up and +Z faces the street.',
      'source_register':f'source/precise/{ID}/reference-review.json','interiors_modeled':False,
      'copyright':'Original geometry MIT. Independent references are documented in the source register.'}
if __name__=='__main__':
    from final_preview import finish
    build(SOURCE,META,PALETTE,make_house)
    finish()
