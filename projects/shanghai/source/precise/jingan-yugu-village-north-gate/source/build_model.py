"""Build the inscribed north gate to Yugu Village on Yuyuan Road."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from north_gate import PALETTE, gate

MODEL_ID = 'jingan-yugu-village-north-gate'
SCOPE = ('愚园路361弄北口的两根名牌门柱、两侧几何石饰和四格铁门。'
         '铁门采用2020年2月闭合形态，另与2017、2019、2021年开启时的实照对照。')
META = {
    'id': MODEL_ID, 'name': '愚谷村愚园路北弄门',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'yugu-village-north-gate.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '门柱中线间距约3.2米，门柱高约2.8米；不同年代影像定位有出入。铁饰、材质与背面按照片比例归纳。',
    'coordinate_convention': 'Local X points to the right when looking in from Yuyuan Road; local Y is inward and local Z is up.',
    'copyright': 'Original geometry and materials, MIT. Sign lettering derives from a renamed Noto Serif CJK subset, SIL OFL 1.1.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['YUGU_GATE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, gate)
