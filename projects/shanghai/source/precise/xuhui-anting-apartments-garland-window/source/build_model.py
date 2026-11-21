"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from garland_window import PALETTE,add_garland_window
META={'id': 'xuhui-anting-apartments-garland-window', 'name': '金司林公寓安亭路底层南窗与垂花饰板', 'viewer_page': 'anting-apartments-garland-window.html', 'scope': '临安亭路首层两扇山花窗中南侧一扇及其独立垂花饰板。', 'model_scope_zh': '带弧形山花的南窗、双扇四格高钢窗、花环饰板及周边少量错缝红褐砖。', 'interiors_modeled': False, 'status': 'photographically-measured-south-window', 'coordinate_convention': 'Metres, positive X toward the south end of the street wall, Y behind the face, Z above the apron bottom.', 'source_register': 'source/precise/xuhui-anting-apartments-garland-window/reference-review.json', 'estimated': '街景两站反算宽、高，栏饰、木叶纹理、铸石出挑和钢材截面以2018年高清照片估计。', 'copyright': 'Original modeled geometry, material colors and renderings. Historical photographs remain separately credited.'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['ANTING_WINDOW_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_garland_window)
