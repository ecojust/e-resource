"""Build the photographed Zhonghua Road frontage of the Lianshi Association."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from association import MATERIALS as PALETTE, add_building

ID = 'huangpu-lianshi-association-east-front'
SCOPE = '依市表4A036与2021年1月8日街景，制作中华路55号的七个街面开间、七座外挑石栏阳台、中轴塔、两翼山墙和临街底层。'
META = {
    'id': ID, 'name': '联市联谊会中华路东立面',
    'viewer_page': 'lianshi-association-east-front.html',
    'status': 'photo-informed-exterior-study', 'scope': SCOPE,
    'model_scope_zh': SCOPE, 'reference_height_m': 19.86,
    'estimated': '三个摄影站110个对应点估算两端山墙约18.57米、中央塔部主檐约19.29米。石雕、短回墙、栏杆厚度及塔上端尺寸根据照片概括；内部、后部和屋顶纵深留待调查。',
    'coordinate_convention': 'Metres, Z up. X along the east frontage northward, Y inland.',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'interiors_modeled': False,
    'copyright': 'Original MIT geometry and materials. References credited separately.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['LIANSHI_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
