"""Build the interwar street entrance and crown of the Astrid Apartments."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from street_corner import PALETTE, build_corner

MODEL_ID = 'huangpu-astrid-apartments-corner'
SCOPE = '茂名南路、南昌路相交处南昌大楼的入口、双列正窗、塔状冠饰及两路紧邻的首段凸窗。后方两条长翼、内院与附房另列。'
META = {
    'id': MODEL_ID, 'name': '南昌大楼（阿斯屈来特公寓）街角入口',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'astrid-apartments.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '短面朝向由文献及长翼内角平分线估配。窗高、色砖大小、门洞内收、冠饰细部及天线高度按街面与高位照片估计。',
    'coordinate_convention': 'Local Y points inward along the bisector of the two street wings. Local X points right from the intersection, local Z points up.',
    'copyright': 'Original geometry and materials, MIT.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['ASTRID_APARTMENTS_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, build_corner)
