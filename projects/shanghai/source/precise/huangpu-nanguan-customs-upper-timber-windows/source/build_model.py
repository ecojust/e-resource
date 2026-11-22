"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from timber_windows import PALETTE,add_building
META={'id': 'huangpu-nanguan-customs-upper-timber-windows', 'name': '江海南关办公楼临街二层红棕色木窗', 'scope': '临街二层的两樘红棕色长窗各有上亮和两扇下窗。右窗上亮留一道绿色木框，两樘白色石窗台向外挑出。', 'model_scope_zh': '临街二层的两樘红棕色长窗各有上亮和两扇下窗。右窗上亮留一道绿色木框，两樘白色石窗台向外挑出。', 'estimated': '木框和格数取自2016年6月18日实照。窗高约2.0米，整段墙宽约3.36米；宽高比例取自原图，绝对尺寸、进深及内侧型材均待实测。', 'viewer_page': 'nanguan-customs-upper-timber-windows.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
