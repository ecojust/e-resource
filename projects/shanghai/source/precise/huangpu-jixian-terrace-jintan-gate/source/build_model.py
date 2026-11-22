"""Build the arched entrance to Jixian Terrace on Jintan Road."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from south_gate import PALETTE, gate

MODEL_ID = 'huangpu-jixian-terrace-jintan-gate'
SCOPE = ('金坛路35弄集贤村南入口，以2021年12月街面图为主并对照2015、2019年的公开街景。'
         '包括两柱、浅弧门额、三格题名、两盏壁灯及一扇留在门面、一扇折向弄内的铁门。')
META = {
    'id': MODEL_ID, 'name': '集贤村金坛路35弄南弄口',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'jixian-terrace-jintan-gate.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '两台2019年街景交会，另与2015年和2021年照片对照。门洞约3.2米宽，门顶约5.5米高。门扇角度、石材深度、灯具剖面和近摄未辨清的铁花按可见轮廓估计。',
    'coordinate_convention': 'Local X points to the right when looking in from Jintan Road; local Y is inward and local Z is up.',
    'copyright': 'Original geometry and materials, MIT. Sign lettering derives from a renamed Noto Serif CJK subset, SIL OFL 1.1.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['JIXIAN_GATE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, gate)
