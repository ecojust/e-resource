"""Build the arched entrance to Yiyuan on Jianguo West Road."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from south_gate import PALETTE, gate

MODEL_ID = 'xuhui-yiyuan-jianguo-road-gate'
SCOPE = ('建国西路506弄的主拱、两扇对合铁门、西侧小拱和东墙五孔。'
         '采用2020年2月闭合形态，题名与门牌参照街景及较近的侧面照片。')
META = {
    'id': MODEL_ID, 'name': '懿园建国西路南门',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'yiyuan-jianguo-road-gate.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '门洞净宽约3.3米，最高瓦脊约4.4米。各年代站点配准有出入，铁花、书体、墙体深度和瓦件按照片比例近似。',
    'coordinate_convention': 'Local X points to the right when looking in from Jianguo West Road; local Y is inward and local Z is up.',
    'copyright': 'Original geometry and materials, MIT. Sign lettering derives from a renamed Noto Serif CJK subset, SIL OFL 1.1.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['YIYUAN_GATE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, gate)
