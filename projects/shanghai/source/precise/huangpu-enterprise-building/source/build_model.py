"""Deliver the seven-bay eastern front of the former Lieu-Ong-Kee office building."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from enterprise_geometry import PALETTE,make_enterprise

ID='huangpu-enterprise-building'
SCOPE='四川中路33号企业大楼，重建东向七开间的黄褐色面砖外墙、山字形阶梯女儿墙、底层大厅拱窗与现状创业大楼门牌。背面及屋顶只按独立源轮廓和航片概化。'
META={'id':ID,'name':'企业大楼（原中国企业银行大楼）','status':'original-photo-informed-exterior',
      'scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'enterprise-building.html',
      'estimated':'按独立源和照片控制主要外廓；竖向高度、面砖接缝、窗下几何凸饰和隐面为比例估计。',
      'coordinate_convention':'Local GLB +X runs north along Middle Sichuan Road, +Y is up and +Z faces east toward the street.',
      'source_register':f'source/precise/{ID}/reference-review.json','interiors_modeled':False,
      'copyright':'Original geometry MIT. Renamed plaque lettering subset SIL OFL 1.1. Images are referenced separately.'}
if __name__=='__main__':
    from final_preview import finish
    build(SOURCE,META,PALETTE,make_enterprise)
    finish()
