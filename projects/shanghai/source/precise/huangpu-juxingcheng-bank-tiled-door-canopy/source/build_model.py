"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-juxingcheng-bank-tiled-door-canopy', 'name': '聚兴诚银行大楼入口瓦门罩与檐下斗栱', 'viewer_page': 'juxingcheng-bank-tiled-door-canopy.html', 'scope': '据江西中路250号街角入口原照制作门罩的前坡、左右斜脊、圆瓦当与檐下斗栱，保留短侧面至贴墙处。', 'model_scope_zh': '据江西中路250号街角入口原照制作门罩的前坡、左右斜脊、圆瓦当与檐下斗栱，保留短侧面至贴墙处。', 'interiors_modeled': False, 'status': 'independent-photograph-based-entry-canopy', 'coordinate_convention': 'X follows the front eave, Y runs back towards the doorway, Z is up.', 'source_register': 'source/precise/huangpu-juxingcheng-bank-tiled-door-canopy/reference-review.json', 'estimated': '门罩沿街宽暂定6.80米。坡深、遮蔽的背面收口、瓦径与斗栱出挑依照片估计；仅处理门罩以上的构件。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['JUXINGCHENG_CANOPY_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
