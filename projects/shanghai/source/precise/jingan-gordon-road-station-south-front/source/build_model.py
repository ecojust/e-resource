"""Build the south courtyard gable of the former Gordon Road Station."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from courtyard import MATERIALS as PALETTE, add_building

ID = 'jingan-gordon-road-station-south-front'
SCOPE = '依据早期两幅馆藏照片与修缮设计单位刊载的南院面正照，制作中央山墙、弧楣门框、分格木窗、左右两段柱廊、石柱头和相接的短屋面。'
META = {
    'id': ID, 'name': '戈登路巡捕房南院面中央山墙与柱廊',
    'viewer_page': 'gordon-road-station-south-front-model.html',
    'status': 'photo-informed-exterior-study', 'scope': SCOPE, 'model_scope_zh': SCOPE,
    'reference_height_m': 15.44,
    'estimated': '原城南面长边实长43.76米。仅建其中约14.50米。高度、柱距、门窗退入量与灰缝按实照比例估计。远端、北墙、其余屋顶和修缮增建的街边玻璃留在原底图。',
    'coordinate_convention': 'Metres, Z up. X follows the south wall toward east-northeast. Y points into the former station.',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'interiors_modeled': False, 'copyright': 'Original geometry and material colours derived from observation. No archive photograph is embedded.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['GORDON_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
