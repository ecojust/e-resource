"""Build the porch, timber oriel and gable of Dingxiang Garden House One."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from porch_gable import PALETTE, add_house

MODEL_ID = 'xuhui-dingxiang-garden-main-house'
SCOPE = ('华山路849号丁香花园一号楼入口局部，含穿通拱廊、连续小拱洞、木窗与牛腿、露木山墙、窗所在的两侧转折及可见屋面。'
         '庭院侧的其余楼体、南廊、其他楼号及园林另列。')
META = {
    'id': MODEL_ID, 'name': '丁香花园一号楼拱廊与露木山墙',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'dingxiang-garden-main-house.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{MODEL_ID}/reference-review.json',
    'estimated': '按2007年已公开的近照和2013年实照推定开间、层高、款式及构件厚度。屋面仅保留山墙后短段和边间可见坡面。',
    'coordinate_convention': 'Local X points to the right when looking in from the garden toward the house. Local Y points inward and local Z points up.',
    'copyright': 'Original geometry and materials, MIT.',
}


if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['DINGXIANG_HOUSE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_house)
