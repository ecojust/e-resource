"""Build the west entrance of Xinen Church from the street survey and dated photograph."""
from argparse import ArgumentParser
from pathlib import Path
import os
import sys
SOURCE = Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from west_porch import PALETTE, add_church
ID = 'jingan-xinen-church-west-porch'
NAME = '新恩堂乌鲁木齐北路尖拱窗与门廊'
SCOPE = '乌鲁木齐北路25号西侧街向山墙与门廊。三开孔与红字、两侧弧券、英文额、三分尖拱窗、坡缘及十字据2015与2020年照片制作。'
META = dict(id=ID,name=NAME,viewer_page='xinen-church-west-porch.html',status='photo-informed-xinen-church-west-porch',scope=SCOPE,model_scope_zh=SCOPE,
            estimated='西廊宽约7.32米、深约6.36米、额顶约5.30米；尖山墙顶约16.09米，脊上十字顶估约18.22米。侧拱内缘和隐藏接头近似。',
            source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,
            coordinate_convention='Metres. Origin at the west porch face. Positive X follows the screen from north to south, positive Y points toward the main church. Z is up.',
            copyright='Original geometry under MIT. The renamed Noto Sans CJK SC font subset is under SIL OFL 1.1. Documentary images have separate credits.')
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest = parser.parse_known_args()
    os.environ['XINEN_PORCH_BLENDER'] = options.blender
    sys.argv[1:] = [*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_church)
