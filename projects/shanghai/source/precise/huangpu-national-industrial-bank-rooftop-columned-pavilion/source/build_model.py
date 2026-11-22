"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-national-industrial-bank-rooftop-columned-pavilion', 'name': '中实大楼屋顶方亭双柱与弧饰额枋', 'viewer_page': 'national-industrial-bank-rooftop-columned-pavilion.html', 'scope': '以中实大楼圆转角上方的最顶层方亭为范围，展示两根圆柱、两端方墩、柱间后退暗面、五组弧形额饰及出挑檐板。', 'model_scope_zh': '以中实大楼圆转角上方的最顶层方亭为范围，展示两根圆柱、两端方墩、柱间后退暗面、五组弧形额饰及出挑檐板。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-national-industrial-bank-rooftop-columned-pavilion/reference-review.json', 'estimated': '以两端方墩外缘间约4.65米为比例。后墙、柱径、柱后进深和檐板后段由正面与少量侧面可见尺度作估计；模型下沿止于圆角楼面题字以上。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['NATIONAL_INDUSTRIAL_BANK_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
