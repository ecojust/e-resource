"""Build the documented 2024–25 entrance to the historic Cathay Theatre."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from corner import PALETTE, add_geometry

ID='huangpu-cathay-cinema'
SCOPE=('淮海中路870号国泰电影院西南路口的阶梯标志塔、竖横排CATHAY字、'
       '2024年重开后的门罩、国泰电影院字标、门厅外侧及相连两段街面。'
       '建筑其余侧后部、完整屋顶、内部影院另计。')
META={'id':ID,'name':'国泰电影院（西南街角与阶梯塔）','viewer_page':'cathay-cinema.html',
      'status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,
      'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
      'coordinate_convention':'Metres. X from Maoming Road to Middle Huaihai Road across the chamfer, Y into the cinema, Z up.',
      'copyright':'Original architecture and materials MIT. Cathay Cinema Sign Subset font under SIL OFL 1.1.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_geometry)
