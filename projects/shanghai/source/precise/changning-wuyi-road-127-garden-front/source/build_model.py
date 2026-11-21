"""Rebuild the historical south garden elevation at 127 Wuyi Road."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from garden_elevation import PALETTE,facade
ID='changning-wuyi-road-127-garden-front'
SCOPE='依据2018年及2024年出版的住宅建筑照片，制作南侧三跨玻璃廊、宝瓶栏杆、窗列、牛腿檐口和折坡屋面的三处老虎窗。'
META={'id':ID,'name':'武夷路127号历史住宅南立面','viewer_page':'wuyi-road-127-history.html','scope':SCOPE,'model_scope_zh':SCOPE,
      'reference_height_m':10.87,'estimated':'立面和檐口比例据公开建筑影像估计。长宁区房管局记始建于1925年，工作名录转录为1932年。',
      'status':'historical-photo-informed-facade-study','source_register':'source/precise/'+ID+'/reference-review.json',
      'coordinate_convention':'X follows the published elevation, Y is section depth, Z is height. No city footprint or model placement.',
      'interiors_modeled':False,'copyright':'Original geometric study. Published reference photographs are not embedded.'}
if __name__=='__main__':build(HERE,META,PALETTE,facade)
