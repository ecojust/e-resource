"""Build the south garden front and tiled roofs of the Zhou residence."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from garden_front import PALETTE, add_house

MODEL_ID = 'huangpu-sinan-road-73-garden-front'
SCOPE = ('思南路73号的庭院正面、底层拱口、两层红棕色木窗及栏杆、两侧可见窗，以及高处照片可核对的红瓦屋面。'
         '室内、西侧临街门墙及其他住宅另列。')
META = {
    'id': MODEL_ID, 'name': '思南路73号周公馆庭院立面',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'sinan-road-73-garden-front.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '以底图轮廓与三版航片对位，窗洞、层高、坡度和出挑由实照估算。屋面背坡根据2020年斜照和航片简化。',
    'coordinate_convention': 'Local X points to the right when looking in from the garden toward the house. Local Y points inward and local Z points up.',
    'copyright': 'Original geometry and materials, MIT.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['SINAN_HOUSE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_house)
