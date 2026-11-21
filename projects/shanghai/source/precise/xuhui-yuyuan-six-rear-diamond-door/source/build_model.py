"""Build the individually attributed back door at Yuyuan no. 6."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from door import PALETTE,add_building
META={'id': 'xuhui-yuyuan-six-rear-diamond-door', 'name': '愉园6号后门菱窗与卷草铁艺', 'viewer_page': 'yuyuan-six-diamond-door.html', 'model_scope_zh': '第四批4D005，愉园，淮海中路1350弄2–16号。制作带“6／一三五〇弄后门”门牌的后门、菱形窗和卷草铁艺。', 'scope': '第四批4D005，愉园，淮海中路1350弄2–16号。制作带“6／一三五〇弄后门”门牌的后门、菱形窗和卷草铁艺。', 'status': 'standalone-registered-door', 'source_register': 'source/precise/xuhui-yuyuan-six-rear-diamond-door/reference-review.json', 'interiors_modeled': False, 'copyright': 'Original door geometry, hand-drawn lettering and materials: MIT. Published reference photographs and archive drawings are separately credited.', 'coordinate_convention': 'Metres. X runs right along the threshold, Y into the house, Z up.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
