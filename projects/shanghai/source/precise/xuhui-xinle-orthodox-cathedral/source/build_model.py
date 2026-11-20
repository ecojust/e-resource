"""Build the Xinle Road cathedral's documented street exterior and five domes."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from sanctuary import PALETTE, add_sanctuary

MODEL_ID = 'xuhui-xinle-orthodox-cathedral'
SCOPE = ('新乐路55号圣母大堂一大四小五座穹顶、北面入口及东面窗墙。'
         '街面采用2011年实拍，并与2013、2020两期街景比照。')
META = {
    'id': MODEL_ID,
    'name': '圣母大堂（新乐路东正教堂）',
    'status': 'original-photo-informed-exterior',
    'viewer_page': 'xinle-orthodox-cathedral.html',
    'scope': SCOPE,
    'model_scope_zh': SCOPE,
    'source_register': 'source/precise/'+MODEL_ID+'/reference-review.json',
    'estimated': '主穹顶高度取地方志35米。鼓座直径、窗数、鼓座和次穹顶高度、窗洞进深、铜皮接缝及背面按照片表现比例估计。',
    'coordinate_convention': 'Metres, Z up in authoring. Positive X follows the north footprint edge east-northeast. Positive Y faces Xinle Road.',
    'interiors_modeled': False,
    'copyright': 'Original exterior geometry under MIT. Source photographs remain with their credited authors.'
}
if __name__=='__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['XINLE_CATHEDRAL_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_sanctuary)
