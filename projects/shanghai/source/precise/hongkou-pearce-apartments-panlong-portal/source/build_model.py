"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from panlong_portal import PALETTE,add_portal
META={'id': 'hongkou-pearce-apartments-panlong-portal', 'name': '浦西公寓蟠龙街26号题名券门', 'viewer_page': 'pearce-apartments-panlong-portal.html', 'scope': '蟠龙街26号单处外侧石券门、红色扇形分格、两扇窄边门及现有横额。', 'model_scope_zh': '蟠龙街26号单处外侧石券门、红色扇形分格、两扇窄边门及现有横额。', 'interiors_modeled': False, 'status': 'independent-historic-fragment', 'coordinate_convention': 'X right when facing street front; Y into courtyard; Z above threshold.', 'source_register': 'source/precise/hongkou-pearce-apartments-panlong-portal/reference-review.json', 'estimated': '门洞宽2.96米为制作比例基准，非现场测量。依据原图门净宽、券高、扇宽排序。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['PANLONG_WINDOW_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_portal)
