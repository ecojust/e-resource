"""Build the three-storey central entrance unit to Shangxianfang."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from gatehouse import PALETTE, make_gatehouse

ID = 'huangpu-shangxianfang-gate'
SCOPE = '淮海中路沿街第一排中跨主弄的门楼，按修缮后的正面照片制作。包括红砖山墙、尚賢坊竖匾、双侧壁柱、石门框与穿楼弄道。范围止于两旁店面共墙和第一排后沿。'
META = {'id':ID,'name':'尚贤坊（淮海中路主弄门楼）','status':'original-photo-informed-exterior',
        'scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'shangxianfang-gate.html',
        'estimated':'2022年上海黄浦正视照片确定立面比例，2005、2014照片辨认题名和原有细部；米制宽高、纵深、背面和瓦色估计。',
        'coordinate_convention':'GLB +X follows Middle Huaihai Road to the northeast, +Y is up, +Z faces the street.',
        'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
        'copyright':'Original geometry MIT. The three outlined glyphs use a renamed SIL OFL 1.1 subset. No photographic textures.'}

if __name__ == '__main__':
    build(SOURCE,META,PALETTE,make_gatehouse)
