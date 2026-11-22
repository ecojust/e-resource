"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from four_pots import PALETTE,add_building
META={'id': 'changning-soong-hongqiao-four-chimney-shafts', 'name': '虹桥路宋氏花园住宅四联切角烟囱与叠帽', 'scope': '近屋脊的宽烟囱，上端并列四支切角筒，三层深浅帽线，下接一圈外挑滴水线和粗抹灰筒身。', 'model_scope_zh': '近屋脊的宽烟囱，上端并列四支切角筒，三层深浅帽线，下接一圈外挑滴水线和粗抹灰筒身。', 'estimated': '按照片将四支烟筒总宽估为1.32米，筒身向上收分、帽线凹凸依据两个视角。取可见的上段，屋顶以下、筒顶内部、烟道实际掏深和另一侧较窄烟囱留待调查，顶面只按外轮廓收边。', 'viewer_page': 'soong-hongqiao-four-chimney-shafts.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the principal facade, local Y points inward, Z is up. Units in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
