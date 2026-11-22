"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable_vent import PALETTE,add_vent
META={'id': 'xuhui-wuyuan-251-arched-gable-vent', 'name': '五原路251号花园住宅山墙拱框百叶窗', 'viewer_page': 'wuyuan-251-arched-gable-vent.html', 'scope': '2013年与2023年照片中右山墙的浅色拱框、后退的横百叶与紧贴窗边的红砖。', 'model_scope_zh': '独立历史装饰构件，右山墙拱框百叶窗。', 'source_register': 'source/precise/xuhui-wuyuan-251-arched-gable-vent/reference-review.json', 'interiors_modeled': False, 'status': 'independent historic architectural detail', 'estimated': '水平尺以邻近砖皮数近似，外框宽约1.04米，误差约0.20米。百叶片数由2013年照片判读，顶端在阴影中。叶角和深度估计。', 'coordinate_convention': 'Metres. X runs along the vent. Y points into the recess and Z is measured from the bottom of the short brick field.', 'copyright': 'Original geometry. Photographs credited separately.'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['WUYUAN_VENT_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_vent)
