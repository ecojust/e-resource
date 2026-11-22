"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from veranda_frame import PALETTE,add_building
META={'id': 'hongkou-tanggu-lane-veranda-knee-braces', 'name': '塘沽路73弄住宅红漆外廊柱、成对斜撑与上层格板', 'scope': '取73弄12号与10号门牌后方可见的红漆外廊一柱。两根斜撑分别向左右承托楼面横梁，廊上右侧有细竖条和错开的短横条，左侧是平直板面。', 'model_scope_zh': '取73弄12号与10号门牌后方可见的红漆外廊一柱。两根斜撑分别向左右承托楼面横梁，廊上右侧有细竖条和错开的短横条，左侧是平直板面。', 'estimated': '高参88于2015年10月27日发布的组照同时拍到两块门牌和相邻廊架。以中柱宽0.18米估计比例，楼面深度、漆面细纹与无法从近照辨明的紧固件尺寸为推估。', 'viewer_page': 'tanggu-lane-veranda-knee-braces.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
