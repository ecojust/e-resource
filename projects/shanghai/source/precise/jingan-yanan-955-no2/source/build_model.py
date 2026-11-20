"""Export the registered house at 2 Lane 955 Yanan Middle Road."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from house_geometry import PALETTE, add_building

ID = 'jingan-yanan-955-no2'
SCOPE = '延安中路955弄2号住宅。2017、2020、2021年街景与多期航片确认北向两扇山墙老虎窗、主瓦坡和向北伸出的低屋面。屋面尺度来自多站估算，树后地面立面及背面开窗为概括。'
META = {'id': ID, 'name': '延安中路955弄2号住宅（北侧老虎窗与凸廊）', 'status': 'original-photo-informed-exterior',
        'viewer_page': 'yanan-955-no2.html', 'scope': SCOPE, 'model_scope_zh': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z-up. +X runs east-northeast along the long ridge and +Y faces the lower north return and Yanan Middle Road.',
        'copyright': 'Original exterior mesh under MIT. Photographs and aerial imagery used as references.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['YANAN_955_HOUSE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
