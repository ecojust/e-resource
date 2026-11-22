"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from brick_corner import PALETTE,add_building
META={'id': 'changning-yuanpei-building-brick-corner', 'name': '元培楼红砖转角窗与叠檐', 'scope': '二层元培楼的临角三樘窗、清水砖与浅色竖向线脚、转折檐口及外置雨水管。', 'model_scope_zh': '二层元培楼的临角三樘窗、清水砖与浅色竖向线脚、转折檐口及外置雨水管。', 'estimated': '长立面节选约4.28米，转角返回约2.12米，高约3.13米。砖缝和型材深度属比例估算；朝向和实尺尚缺测绘控制。', 'viewer_page': 'yuanpei-building-brick-corner.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the principal facade, local Y points inward, Z is up. Units in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
