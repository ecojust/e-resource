"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from gable import PALETTE,model
META={'id': 'jingan-wujin-580-pediment-and-paired-window-heads', 'name': '武进路580号住宅临街小山花窗与双券窗楣', 'viewer_page': 'wujin-580-pediment-and-paired-window-heads.html', 'scope': '阅读静安逐号标注武进路580号的临街图像左侧，复现小山花的上层方窗和相邻较低的两枚拱形窗楣。', 'model_scope_zh': '阅读静安逐号标注武进路580号的临街图像左侧，复现小山花的上层方窗和相邻较低的两枚拱形窗楣。', 'interiors_modeled': False, 'status': 'independent-photograph-based-facade-detail', 'coordinate_convention': 'X follows the photographed street elevation, Y recedes into the front wall, Z is up.', 'source_register': 'source/precise/jingan-wujin-580-pediment-and-paired-window-heads/reference-review.json', 'estimated': '各部尺寸取自原照相对比例，端部山花面宽约取2.60米。原墙赤色、石质封檐与窗框色来自区级资料中的街面照片，进深、券石分缝和窗后暗处为示意。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['WUJIN_PEDIMENT_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
