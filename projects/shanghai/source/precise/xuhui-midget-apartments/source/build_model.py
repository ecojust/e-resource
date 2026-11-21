"""Build the Midget Apartments at Wukang and Hunan Roads."""
import argparse
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from corner_front import PALETTE, add_corner

ID = 'xuhui-midget-apartments'
SCOPE = '据2013、2015和2026年街照建密丹公寓截角立面和两侧短墙，包含两樘顶层竖窗、横窗、二层深窗和成对阶形托块。首层店面参照2026年，后院及余下两街立面待补。'
META = dict(id=ID, name='密丹公寓武康路与湖南路转角立面', status='original-photo-informed-partial-exterior',
            viewer_page='midget-apartments.html', scope=SCOPE, model_scope_zh=SCOPE,
            interiors_modeled=False, source_register=f'source/precise/{ID}/reference-review.json',
            estimated='临街原始多边形和独立门牌控制平面，檐高参照冻结城市原楼，墙洞、窗格和挑块按照片估计。',
            coordinate_convention='Local +X follows the clipped corner from the Wukang side to the Hunan side. +Y points into the building and +Z upwards.',
            copyright='Original MIT geometry and materials. Documentary photographs are cited by URL.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['MIDGET_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_corner)
