"""Build the garden elevation of Donghu Hotel House Seven."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from garden_elevation import PALETTE, add_house

MODEL_ID = 'xuhui-donghu-hotel-house-seven'
SCOPE = ('淮海中路1110号东湖宾馆七号楼朝花园的三段立面，包括弧拱窗、垂花、爱奥尼亚双柱、窗前铁栏、屋顶老虎窗、玻璃廊及石阶。'
         '所绘外廊和屋顶层以照片中的现状为准，侧门廊及屋后另列。')
META = {
    'id': MODEL_ID, 'name': '东湖宾馆七号楼花园立面',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'donghu-house-seven.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '以底图南墙长度、现场外观照及高位屋顶照片估计窗柱比例、玻璃廊进深和坡度。',
    'coordinate_convention': 'Local X points to the right when looking in from the garden toward the house. Local Y points inward and local Z points up.',
    'copyright': 'Original geometry and materials, MIT.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['DONGHU_HOUSE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_house)
