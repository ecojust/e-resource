"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from portal import PALETTE,model
META={'id': 'changning-customs-commissioner-east-portal', 'name': '上海海关税务司住宅东门砖砌喇叭口与石券罩', 'viewer_page': 'customs-commissioner-east-portal.html', 'scope': '江苏路162弄3号东山墙的门洞，含红砖喇叭口、双牛腿挑出石罩和向上收进的弧形石阶。', 'model_scope_zh': '上海海关税务司住宅东门砖砌喇叭口与石券罩', 'interiors_modeled': False, 'status': 'photograph-based-architectural-detail', 'coordinate_convention': 'X runs along the east entrance wall, Y towards the room, Z upright.', 'source_register': 'source/precise/changning-customs-commissioner-east-portal/reference-review.json', 'estimated': '以双扇内门估宽1.20米，从正面和斜视照片比对券罩、进深、踏步与门牌比例。绝对尺寸为估计值。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['JIANGSU_PORTAL_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
