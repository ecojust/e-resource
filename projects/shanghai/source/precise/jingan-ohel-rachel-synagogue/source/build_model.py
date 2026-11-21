"""Build the Ohel Rachel Synagogue at its present Shanghai compound."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from synagogue import PALETTE, add_building

ID = 'jingan-ohel-rachel-synagogue'
SCOPE = '按世界古迹基金会航拍、1920至1930年代影像及2013至2026年入口实拍，重建院内东向爱奥尼双柱凹廊、山墙半圆窗、两翼环窗和南北侧拱窗与瓦顶。未见后墙细部采用简面，尺寸据照片及足迹估算。'
META = dict(id=ID,name='西摩路会堂（拉结会堂院内柱廊与侧窗）',status='photo-informed-synagogue-exterior',viewer_page='ohel-rachel-synagogue.html',scope=SCOPE,model_scope_zh=SCOPE,source_register='source/precise/'+ID+'/reference-review.json',interiors_modeled=False,all_dimensions_estimated=True,coordinate_convention='Metres, Z up; local negative Y points east-northeast, toward the two-column entry portico and campus courtyard.',copyright='Original architectural mesh under MIT. Reference photographs are not embedded.')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['OHEL_RACHEL_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
