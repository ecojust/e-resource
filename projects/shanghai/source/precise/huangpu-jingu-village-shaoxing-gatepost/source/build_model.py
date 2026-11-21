"""Build the Shaoxing Road lane marker from the photographed lettering and masonry courses."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from inscribed_pier import PALETTE,add_building
META={'id': 'huangpu-jingu-village-shaoxing-gatepost', 'name': '金谷邨绍兴路18弄南入口题名门柱', 'viewer_page': 'jingu-village-gatepost.html', 'status': 'photo-informed-gatepost', 'model_scope_zh': '第四批4C020，绍兴路18弄。两处2020年街景可读18弄1–83及金谷邨三字，制作南入口题名柱、门牌与相连素色壁框。', 'scope': '第四批4C020，绍兴路18弄。两处2020年街景可读18弄1–83及金谷邨三字，制作南入口题名柱、门牌与相连素色壁框。', 'interiors_modeled': False, 'source_register': 'source/precise/huangpu-jingu-village-shaoxing-gatepost/reference-review.json', 'estimated': '2020年2月两站可以辨认题名、门牌和石材分格。柱头背侧及门牌阴影以内的厚度由侧面视差估计。', 'copyright': 'Original architectural geometry and hand-drawn lettering under MIT. The reference images are identified separately.', 'coordinate_convention': 'Metres, Z up. X increases to the viewer’s right, Y from the inscription into the lane.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
