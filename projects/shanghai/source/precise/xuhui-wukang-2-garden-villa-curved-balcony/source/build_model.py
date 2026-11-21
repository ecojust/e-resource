"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from balcony import PALETTE,add_building
META={'id': 'xuhui-wukang-2-garden-villa-curved-balcony', 'name': '武康路2号花园住宅南向弧形阳台与双柱', 'viewer_page': 'wukang-2-curved-balcony.html', 'status': 'photo-informed-architectural-component', 'model_scope_zh': '院内主楼南面中跨，自花园铺地下缘至弧形阳台扶手，含双柱、圆弧板、浅色分隔柱、绿色开孔金属栏和退入的门廊。', 'scope': '院内主楼南面中跨，自花园铺地下缘至弧形阳台扶手，含双柱、圆弧板、浅色分隔柱、绿色开孔金属栏和退入的门廊。', 'interiors_modeled': False, 'source_register': 'source/precise/xuhui-wukang-2-garden-villa-curved-balcony/reference-review.json', 'estimated': '端部和进深按2024正射及园内正面资料图估计。', 'coordinate_convention': 'X increases to the viewer’s right. Positive Y goes from the garden into the portico. Z is measured above the porch paving.', 'copyright': 'Original geometry and analytic materials, MIT. Documentary image rights remain with their respective authors.'}

if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
