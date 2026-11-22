"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from garden_loggia import PALETTE,add_building
META={'id': 'changning-fushi-garden-faceted-loggia', 'name': '福世花园园侧折线浅拱敞廊与铁栏', 'scope': '花园一侧二层敞廊的五段折线券底、外挑窗台、分叉花铁栏和后退的两樘玻璃门窗。', 'model_scope_zh': '花园一侧二层敞廊的五段折线券底、外挑窗台、分叉花铁栏和后退的两樘玻璃门窗。', 'estimated': '廊口按照片比例估计，净宽约3.58米，栏顶高约1米，后排门窗与栏杆相距约1.2米。被树枝和衣物遮挡的栏花间距与末端以照片中的重复间距推估。两张同栋照片可核，具体门牌缺独立可读证据。', 'viewer_page': 'fushi-garden-faceted-loggia.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the principal facade, local Y points inward, Z is up. Units in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
