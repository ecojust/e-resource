"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from triple_parapet import PALETTE,add_building
META={'id': 'changning-yang-garden-triple-parapet', 'name': '杨氏花园南立面三弧山花与双扇窗', 'scope': '花园南立面顶层的三个半圆山花、上下叠线、三樘双扇窗及窗下浅饰板。', 'model_scope_zh': '花园南立面顶层的三个半圆山花、上下叠线、三樘双扇窗及窗下浅饰板。', 'estimated': '据影像比例估算此段宽6.74米，从底部水平线至中间弧顶约3.8米；窗框的内部木、钢基材及背部厚度无图纸量测。', 'viewer_page': 'yang-garden-triple-parapet.html', 'interiors_modeled': False, 'coordinate_convention': 'X follows the south elevation, Y points into the building and Z is upward. Units are metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
