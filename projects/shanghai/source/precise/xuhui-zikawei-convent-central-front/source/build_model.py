from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / "tools"))
from package_architectural_model import build
from convent_front import PALETTE, facade

META = {'id': 'xuhui-zikawei-convent-central-front', 'name': '徐家汇圣母院旧主楼庭院中央山花立面', 'viewer_page': 'zikawei-convent-central-front.html', 'status': 'original-photo-informed-exterior', 'scope': '院侧大山花与四开间上层窗墙、两段短退进窗墙、西侧在树间可辨的两开间玻璃廊。', 'model_scope_zh': '庭院中央四开间山花，依照2016年影像显示可辨部分。', 'estimated': '中央开间节奏、山花小孔与百叶取自2016年院内斜上方照片，绝对尺度、颜色及投影深度为估计。', 'source_register': 'source/precise/xuhui-zikawei-convent-central-front/reference-review.json', 'interiors_modeled': False, 'coordinate_convention': 'X runs to the right of the principal garden photograph, Y into the old house and Z up, in metres.', 'copyright': 'Original geometric interpretation and materials, MIT.'}

if __name__ == "__main__":
    build(HERE, META, PALETTE, facade)
