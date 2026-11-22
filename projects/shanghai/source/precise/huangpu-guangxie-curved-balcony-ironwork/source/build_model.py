"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from iron_circles import PALETTE,add_building
META={'id': 'huangpu-guangxie-curved-balcony-ironwork', 'name': '广协书局大楼转角阳台圆环铁栏', 'scope': '转角阳台临街的一段铁栏，含六组圆环、环内四瓣内凹曲线、中心小方框和贯通的扶手。圆弧形石板压顶位于黑漆铁栏下方。', 'model_scope_zh': '转角阳台临街的一段铁栏，含六组圆环、环内四瓣内凹曲线、中心小方框和贯通的扶手。圆弧形石板压顶位于黑漆铁栏下方。', 'estimated': '六跨长约2.76米，取自2015年署名照片和现场街景的可见比例。栏高、转角半径和型材厚度为估计值。', 'viewer_page': 'guangxie-curved-balcony-ironwork.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
