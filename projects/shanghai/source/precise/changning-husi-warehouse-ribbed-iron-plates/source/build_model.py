"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from wall_belt import PALETTE,add_building
META={'id': 'changning-husi-warehouse-ribbed-iron-plates', 'name': '湖丝栈灰砖厂房放射纹铁板与砖腰线', 'viewer_page': 'husi-warehouse-ribbed-iron-plates.html', 'scope': '节选灰砖外墙上两块并列的深色放射纹铁板及其两侧、上下的红褐阶砖和灰色外挑压顶。', 'model_scope_zh': '节选灰砖外墙上两块并列的深色放射纹铁板及其两侧、上下的红褐阶砖和灰色外挑压顶。', 'status': 'photo-informed-architectural-component', 'estimated': '按砖高与窗口相对尺度近似；图像未提供原尺寸。', 'interiors_modeled': False, 'coordinate_convention': 'X runs along the wall, positive Y points behind the ironwork and Z is up. Distances in metres.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
