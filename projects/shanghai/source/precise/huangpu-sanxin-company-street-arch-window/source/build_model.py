"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'huangpu-sanxin-company-street-arch-window', 'name': '中新公司大楼沿街石券窗与铁窗栅', 'viewer_page': 'sanxin-company-street-arch-window.html', 'scope': '取一樘沿街底层大券窗、两侧横缝石墩、分块拱券、叠线窗台、窗裙与窗前铁栅。', 'model_scope_zh': '取一樘沿街底层大券窗、两侧横缝石墩、分块拱券、叠线窗台、窗裙与窗前铁栅。', 'interiors_modeled': False, 'status': 'photographed-street-elevation-fragment', 'coordinate_convention': 'X follows the photographed facade, Y increases backwards, Z is up.', 'source_register': 'source/precise/huangpu-sanxin-company-street-arch-window/reference-review.json', 'estimated': '窗洞按约2米宽估尺。石块面宽、灰缝宽、铁栅进深和杆径根据2015及2021两幅沿街原照的可见比例近似，后侧墙体限于可见窗洞厚度。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['SANXIN_ARCH_WINDOW_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
