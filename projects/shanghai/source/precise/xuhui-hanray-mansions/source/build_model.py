"""Build the stepped Huaihai Road frontage of Hanray Mansions."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from huaihai_front import PALETTE, build_front

MODEL_ID = 'xuhui-hanray-mansions'
SCOPE = '淮海中路1162号沿街中央入口、两组横窗、竖向砖带和上部圆角露台。后楼、附房和屋面设备另查。'
META = {
    'id': MODEL_ID, 'name': '亨利公寓（淮中大楼）淮海中路门面与弧形露台',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'hanray-mansions.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '沿街方向以独立建筑轮廓及道路定向，窗高、门口曲线、分格及露台半径按街景和高位照片估配。',
    'coordinate_convention': 'Local Y points inward from Middle Huaihai Road. X follows the frontage toward the east and Z points up.',
    'copyright': 'Original geometry and materials, MIT.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['HANRAY_MANSIONS_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, build_front)
