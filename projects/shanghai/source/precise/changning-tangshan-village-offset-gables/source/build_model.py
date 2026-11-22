"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'changning-tangshan-village-offset-gables', 'name': '汤山村弄内住宅错落双山墙', 'viewer_page': 'tangshan-village-offset-gables.html', 'scope': '规资局标明汤山村的照片中，两座前后错落的小山墙、尖端装饰、绿漆檐板与竖条窗。', 'model_scope_zh': '规资局标明汤山村的照片中，两座前后错落的小山墙、尖端装饰、绿漆檐板与竖条窗。', 'interiors_modeled': False, 'status': 'photograph-based-architectural-detail', 'coordinate_convention': 'X follows the principal visible elevation, Y recedes into the roof and Z points up.', 'source_register': 'source/precise/changning-tangshan-village-offset-gables/reference-review.json', 'estimated': '小山墙略向后，檐口较低。前后距离和绝对尺寸为估计。照片未在这些山墙标出分户门牌。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['TANGSHAN_GABLE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
