"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from hall import PALETTE,model
META={'id': 'changning-zhou-residence-curved-window-hall', 'name': '周氏花园住宅弧窗厅木圆柱与格扇', 'viewer_page': 'zhou-residence-curved-window-hall.html', 'scope': '愚园路1015号历史住宅厅内窗弧的可见中段。四组格扇、两根暖棕色凹槽圆柱、柱头与窗头线脚按区规资局室内原图绘制。', 'model_scope_zh': '厅内弧窗中段与两端木色圆柱', 'interiors_modeled': True, 'status': 'photograph-based-architectural-detail', 'coordinate_convention': 'X across window opening; Y away from the interior; Z upright. Lower edge cuts at the photograph’s visible part of the shafts.', 'source_register': 'source/precise/changning-zhou-residence-curved-window-hall/reference-review.json', 'estimated': '以可见内窗宽约3.5米定展示比例。平面弧度、柱径与画面外的框底为估计。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['ZHOU_CURVED_HALL_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
