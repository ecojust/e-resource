"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-lawyers-club-chevron-spandrels', 'name': '上海律师公会会所双列钢窗与人字纹窗裙', 'viewer_page': 'lawyers-club-chevron-spandrels.html', 'scope': '取银行博物馆入口上方三层成对窗、分隔窗间的反向斜纹窗裙及双块压顶。窗下边界为首道斜纹窗裙。', 'model_scope_zh': '取银行博物馆入口上方三层成对窗、分隔窗间的反向斜纹窗裙及双块压顶。窗下边界为首道斜纹窗裙。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-lawyers-club-chevron-spandrels/reference-review.json', 'estimated': '以两扇并排钢窗单扇宽约0.92米为比例参照。窗裙出墙量、窗格内陷和屋顶两块压顶进深按仰视照片估计。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['LAWYERS_CLUB_CHEVRONS_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
