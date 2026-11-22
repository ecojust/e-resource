"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from fluted_capitals import PALETTE,add_building
META={'id': 'huangpu-fair-building-dianchi-fluted-capitals', 'name': '公平大楼滇池路巨柱柱头与三槽檐带', 'scope': '滇池路街面巨柱的上端有石刻竖槽，圆形柱颈上承曲面的柱头和方石板。两根相邻柱头之上的檐梁留有成组三道的短竖槽，顶缘分层挑出。', 'model_scope_zh': '滇池路街面巨柱的上端有石刻竖槽，圆形柱颈上承曲面的柱头和方石板。两根相邻柱头之上的檐梁留有成组三道的短竖槽，顶缘分层挑出。', 'estimated': '取相邻两根巨柱的上端和其间一跨檐梁。柱径按照片估约0.55米，柱距约1.78米；竖槽的数量、石材颜色和线脚深度按街面可辨轮廓近似。此为局部细节，未测整楼尺寸。', 'viewer_page': 'fair-building-dianchi-fluted-capitals.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
