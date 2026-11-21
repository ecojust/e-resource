"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from dormers import PALETTE,add_dormers
META={'id': 'xuhui-dongping-eleven-mansard-dormers', 'name': '东平路11号宋氏住宅南坡三扇老虎窗', 'viewer_page': 'dongping-eleven-mansard-dormers.html', 'scope': '东平路11号花园主宅南坡三扇带山花的老虎窗，含两扇式木窗、叠层窗套、侧壁及相连的红瓦屋面。', 'model_scope_zh': '东平路11号花园主宅南坡三扇带山花的老虎窗，含两扇式木窗、叠层窗套、侧壁及相连的红瓦屋面。', 'source_register': 'source/precise/xuhui-dongping-eleven-mansard-dormers/reference-review.json', 'interiors_modeled': False, 'status': 'photo-measured-roof-fragment', 'estimated': '三条窗轴线取自园内主屋航片，间距约3.8米；窗宽和叠线高度按修缮后正面原照片比例还原，南阳台遮住的一小段下槛经过估计。', 'coordinate_convention': 'Metres. X runs from the west dormer to the east dormer. Positive Y follows the slope inward. Z starts at the lower edge of the photographed roof strip.', 'copyright': 'Original modeled surfaces. Historical and contemporary photographs are cited separately.'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['DONGPING_DORMERS_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_dormers)
