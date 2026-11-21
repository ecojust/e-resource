"""Export the 1938 Guo Dihuo west house."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from house_geometry import PALETTE, add_building

ID = 'xuhui-guo-dihuo-west-house'
SCOPE = '华山路893号郭棣活旧居的1938年西楼，现899号。按修缮实照与湖南街道地方史重建东南弧窗、曲尺形阳台及舌形雨厦。立面尺度、背面和枝叶遮挡部分按航片和照片比例估算。'
META = {'id': ID, 'name': '郭棣活旧居西楼（东南花园立面）', 'status': 'original-photo-informed-exterior',
        'viewer_page': 'guo-dihuo-west-house.html', 'scope': SCOPE, 'model_scope_zh': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z-up. Positive X follows the long roof towards east-northeast. The curved garden front faces negative Y, south-southeast.',
        'copyright': 'Original architectural mesh under MIT. External photographs and aerial images used only as references.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['GUO_WEST_HOUSE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
