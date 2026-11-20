"""Build the three-storey street frontage of the 1925 Shanghai Chinese Banking Association."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from association import PALETTE, add_frontage

ID = 'huangpu-bankers-association-building'
SCOPE = '香港路59号三层石立面，五开间门廊、四根圆柱及两端带槽壁柱、退入的门窗、成对花环和屋顶盾饰。两侧和后方以有界剖面收口。'
META = {
    'id': ID, 'name': '银行公会大楼（香港路五开间柱廊）',
    'viewer_page': 'bankers-association.html', 'status': 'original-photo-informed-exterior',
    'scope': SCOPE, 'model_scope_zh': SCOPE,
    'estimated': '香港路北立面宽约21.8米。门廊高度、进深、柱槽及柱头花叶参照2014及2018年影像比例估计。',
    'coordinate_convention': 'GLB +Z toward Hong Kong Road (NNW), +X along the street toward WSW, +Y up.',
    'interiors_modeled': False, 'source_register': f'source/precise/{ID}/reference-review.json',
    'copyright': 'Original geometry MIT. No photographs embedded.'
}

if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_frontage)
