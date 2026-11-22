"""Build the photographed central foyer and spire of the Shanghai Exhibition Centre."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from foyer import PALETTE, add_building

ID = 'jingan-sino-soviet-central-foyer'
SCOPE = '南广场可见的方形序馆、中央拱门、两侧金顶小塔、列柱塔层、鎏金钢塔和红五星。'
META = {
    'id': ID, 'name': '中苏友好大厦南广场序馆与中央塔楼',
    'viewer_page': 'sino-soviet-central-foyer.html',
    'status': 'photo-informed-exterior-study', 'scope': SCOPE,
    'model_scope_zh': SCOPE, 'reference_height_m': 114.,
    'estimated': '地方志载原中央大厅平面为46米见方，钢塔标高110.4米。修缮采访称星顶距地约114米。各层开间、塔身收分、外墙装饰和侧面尺度依多期公开照片估算。',
    'coordinate_convention': 'Metres, Z up. The origin is the middle of the south court frontage. X follows the facade eastward, Y follows the plaza axis northward.',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'interiors_modeled': False,
    'copyright': 'Original MIT geometry and materials. References and the OFL lettering font are credited separately.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['FOYER_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
