"""Package the paired street facades and the specific 48 Gaoan Road entrance of Washington Apartments."""
import argparse
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from street_fronts import PALETTE, add_apartment

ID = 'xuhui-washington-apartments'
SCOPE = ('依据2016年转角实照、2020年街景和徐汇区房管材料制作衡山路与高安路的街角窗列、阶梯冠部、'
         '高安路48号入口的白色退台门框、花纹窗间墙与两侧凸窗。西部其余门牌、院侧与室内另列。')
META = dict(id=ID, name='华盛顿公寓衡山路街角与高安路48号入口',status='original-photo-informed-partial-exterior',
            viewer_page='washington-apartments.html', scope=SCOPE, model_scope_zh=SCOPE,
            interiors_modeled=False, source_register=f'source/precise/{ID}/reference-review.json',
            estimated='两段街面随实名原楼轮廓，1930年主体及1982年加层的现状高度、窗间尺寸、门廊装饰依照片比例估算。',
            coordinate_convention='Local +X follows the truncated north corner toward WNW, +Y enters the street corner toward SSW, +Z is up.',
            copyright='Original MIT geometry and materials. Documentary photographs are cited by URL.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['WASHINGTON_APARTMENTS_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_apartment)
