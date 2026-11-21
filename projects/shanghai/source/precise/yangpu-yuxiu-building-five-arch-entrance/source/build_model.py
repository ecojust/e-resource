"""Rebuild both editable-level geometries and their independent viewer assets."""
from argparse import ArgumentParser
from pathlib import Path
import os,sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(Path(os.environ.get('SHANGHAI_PROJECT_ROOT',SOURCE.parents[3]))/'tools'))
from package_architectural_model import build
from portal import PALETTE,model
META={'id': 'yangpu-yuxiu-building-five-arch-entrance', 'name': '毓秀楼正门五券石廊', 'viewer_page': 'yuxiu-building-five-arch-entrance.html', 'scope': '正面底层五券、六处墩座、内退三道玻璃门、两侧菱格窗与毓秀樓题字。', 'model_scope_zh': '上海财经大学毓秀楼正面门廊', 'interiors_modeled': False, 'status': 'photograph-based-architectural-detail', 'coordinate_convention': 'X runs along the arcade, Y runs in through the entry, Z is vertical.', 'source_register': 'source/precise/yangpu-yuxiu-building-five-arch-entrance/reference-review.json', 'estimated': '以单开间中心距约2.52米估测；进深、门内框架、石料色与题字字形为近似。'}
if __name__=='__main__':
    ap=ArgumentParser(add_help=False);ap.add_argument('--blender',default='blender');opt,rest=ap.parse_known_args()
    os.environ['YUXIU_BLENDER']=opt.blender;sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,model)
