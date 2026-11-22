"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from stepped_gate import PALETTE,add_building
META={'id': 'jingan-bank-of-china-warehouse-stepped-gate', 'name': '中国银行仓库双扇阶格式金属大门', 'scope': '两扇黑漆金属门各有四块横向实心框板。窄横档和短竖梃在框板间相接，形成能透视的阶梯形空格。', 'model_scope_zh': '两扇黑漆金属门各有四块横向实心框板。窄横档和短竖梃在框板间相接，形成能透视的阶梯形空格。', 'estimated': '依据门扇修缮前后正面照片绘制。两扇合宽约2.0米、门扇高约2.1米，按照片估算；门后空间未测。', 'viewer_page': 'bank-of-china-warehouse-stepped-gate.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
