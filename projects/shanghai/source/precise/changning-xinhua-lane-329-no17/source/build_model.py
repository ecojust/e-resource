"""Build the two photographed elevations of house 17 in Lane 329 on Xinhua Road."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from spanish_villa import PALETTE, add_house

MODEL_ID = 'changning-xinhua-lane-329-no17'
SCOPE = ('新华路329弄17号西侧入口、尖券车库和南侧的花园廊、露台、三层间与红筒瓦屋面。北侧和东侧仅表现外轮廓，树后细节与内部另列。')
META = {
    'id': MODEL_ID, 'name': '新华路329弄17号住宅',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'xinhua-lane-329-no17.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '西侧入口照片、南花园旧照与标北地块图用于估配开间。窗门尺度、纵深、倾角、瓦距与树后轮廓均为估计。',
    'coordinate_convention': 'Local X points to the right when looking in from the west lane toward the entrance. Local Y points inward and local Z points up.',
    'copyright': 'Original geometry and materials, MIT.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['XINHUA_17_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_house)
