"""Make the present eight-storey New Asia Hotel streetscape at Tiantong and North Sichuan Roads."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from hotel_geometry import PALETTE,make_hotel

ID='hongkou-new-asia-hotel'
SCOPE='天潼路422号新亚酒楼现存临街主楼，含天潼路长翼、四川北路短翼、圆弧转角主入口及退台塔楼。共墙之后的独立屋面、历史副楼归属和旅馆内部另列。'
META={'id':ID,'name':'新亚酒楼（上海新亚大酒店临街主楼）','status':'original-photo-informed-exterior',
      'scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'new-asia-hotel.html',
      'estimated':'以现状具名酒店与冻结楼面外轮廓约束平面。层高、檐口进退、后墙、屋面设备与招牌字形按照片和航片估计。',
      'coordinate_convention':'glTF +X follows Tiantong Road to the northeast, +Y goes up, +Z faces the street to the southeast.',
      'source_register':f'source/precise/{ID}/reference-review.json','interiors_modeled':False,
      'copyright':'Original geometry MIT. Roof and entrance lettering uses a renamed SIL OFL 1.1 font subset; imagery is referenced separately.'}
if __name__=='__main__':
    from final_preview import finish
    build(SOURCE,META,PALETTE,make_hotel)
    finish()
