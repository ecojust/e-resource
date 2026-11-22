"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from inscribed_panel import PALETTE,add_building
META={'id': 'changning-qishan-village-inscribed-stone-panel', 'name': '岐山村1032弄入口金字题名与石框', 'scope': '街口石框的矩形凹槽、从右向左排列的三个金字、绿色路牌和四角固定件。', 'model_scope_zh': '街口石框的矩形凹槽、从右向左排列的三个金字、绿色路牌和四角固定件。', 'estimated': '石框宽约1.68米，露出的上段高约1.08米。金字和路牌根据正面照片比例重新绘制，绝对尺寸与背面厚度为估计值。', 'viewer_page': 'qishan-village-inscribed-stone-panel.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the principal facade, local Y points inward, Z is up. Units in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
