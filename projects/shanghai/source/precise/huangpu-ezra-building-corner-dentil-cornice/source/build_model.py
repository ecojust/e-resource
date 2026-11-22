"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-ezra-building-corner-dentil-cornice', 'name': '新康大楼街角双层石窗与齿饰檐口', 'viewer_page': 'ezra-building-corner-dentil-cornice.html', 'scope': '以2015年具名街景中可见的切角一开间为范围，包括两层方窗、下窗上方托块、绕角的檐板与短齿，以及檐上可见的垂花饰。', 'model_scope_zh': '以2015年具名街景中可见的切角一开间为范围，包括两层方窗、下窗上方托块、绕角的檐板与短齿，以及檐上可见的垂花饰。', 'interiors_modeled': False, 'status': 'independent-photograph-based-facade-detail', 'coordinate_convention': 'X follows the photographed street elevation, Y recedes into the front wall, Z is up.', 'source_register': 'source/precise/huangpu-ezra-building-corner-dentil-cornice/reference-review.json', 'estimated': '中央立面宽暂取3.0米。侧翼转折角、窗内分格退深、檐齿与垂花伸出尺寸据照片比例估计。施工覆盖部分止于实照。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['EZRA_CORNICE_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
