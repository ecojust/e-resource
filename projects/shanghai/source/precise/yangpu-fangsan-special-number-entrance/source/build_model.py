"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from entrance import PALETTE,model
META={'id': 'yangpu-fangsan-special-number-entrance', 'name': '纺三小区特号住宅门廊与石阶', 'viewer_page': 'fangsan-special-number-entrance.html', 'scope': '许昌路227弄特号面向圆形绿地的入口，含七级石阶、两道斜杆、方柱、平挑雨篷、绿底特号牌及门上楼梯窗。', 'model_scope_zh': '纺三特号住宅主入口与正上方窄窗。', 'status': 'historical-photograph-reconstruction', 'interiors_modeled': False, 'coordinate_convention': 'X follows the front and Y runs toward the doorway. Z is height from the courtyard approach.', 'source_register': 'source/precise/yangpu-fangsan-special-number-entrance/reference-review.json', 'estimated': '门高和踏步高度取常用范围作相片尺度估算。雨篷进深、遮挡后的柱身、门扇、墙厚及栏杆直径按照片约束。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['FANGSAN_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
