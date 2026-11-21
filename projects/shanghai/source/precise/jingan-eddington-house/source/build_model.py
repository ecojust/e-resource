"""Build the stepped street elevation of Eddington House on Changde Road."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from apartment_elevations import PALETTE, add_house

MODEL_ID = 'jingan-eddington-house'
SCOPE = '常德路195号爱登公寓的东立面、两侧圆角长阳台、上层退台、中央窗柱与入口题字门廊。后部两短翼与屋面按文献及俯视照片概括，室内与修缮分期另列。'
META = {
    'id': MODEL_ID, 'name': '爱登公寓（常德公寓）',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'eddington-house.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '本栋现有地块及2013至2026年外观照片决定总体宽度和层次。层高、横带、曲线半径、背部天井和屋面尺寸按比例估计。',
    'coordinate_convention': 'Local X points to the right when looking in from Changde Road toward the east elevation. Local Y points inward and local Z points up.',
    'copyright': 'Original geometry and materials, MIT. Renamed lettering subset, SIL OFL 1.1.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['EDDINGTON_HOUSE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_house)
