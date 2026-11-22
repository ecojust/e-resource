"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'changning-1931-blind-school-historic-name-plaque', 'name': '虹桥路旧盲童学校1931年“盲童學校”横匾', 'viewer_page': '1931-blind-school-historic-name-plaque.html', 'scope': '只展出1931年虹桥路旧址历史照片上方的横匾、四个可读题字和少量周围砖面。两端细小题署留其可辨墨迹。', 'model_scope_zh': '只展出1931年虹桥路旧址历史照片上方的横匾、四个可读题字和少量周围砖面。两端细小题署留其可辨墨迹。', 'interiors_modeled': False, 'status': 'independent-archival-inscription', 'coordinate_convention': 'X follows the tablet, Y recedes behind the tablet, Z is up.', 'source_register': 'source/precise/changning-1931-blind-school-historic-name-plaque/reference-review.json', 'estimated': '横匾宽暂取2米，长宽比按档案画面校正。墨字的实际施作方法、砖与底板的原色和深度无法从黑白原照测定。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['HISTORICAL_PLAQUE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
