"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from parapet import PALETTE,add_building
META={'id': 'yangpu-ye-garden-white-hall-pierced-parapet', 'name': '叶家花园小白楼廊前几何镂空栏板', 'viewer_page': 'ye-garden-white-hall-pierced-parapet.html', 'scope': '小白楼花园立面左段，两个方墩之间的几何透孔栏板、上下压边和墩面矩形线脚。', 'model_scope_zh': '小白楼花园立面左段，两个方墩之间的几何透孔栏板、上下压边和墩面矩形线脚。', 'status': 'photo-informed-architectural-component', 'interiors_modeled': False, 'estimated': '栏板高约1.06米，两墩中心距按3.26米设比；未取得实测平面或现场尺。', 'coordinate_convention': 'X follows the gallery edge, Y points towards the gallery and Z points up. Dimensions are in metres.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
