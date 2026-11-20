"""Package the river-facing five-bay façade at 29 Zhongshan East 1st Road."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from riverfront import PALETTE, add_riverfront

ID = 'huangpu-banque-de-lindochine'
SCOPE = '外滩29号现存东向五开间石立面，包括中央门洞、两根巨柱、二层窗廊、檐线和顶栏。两端及后部以浅剖面收口。'
META = {
    'id': ID, 'name': '东方汇理银行（外滩29号临江立面）',
    'viewer_page': 'banque-de-lindochine.html', 'status': 'original-photo-informed-exterior',
    'scope': SCOPE, 'model_scope_zh': SCOPE,
    'estimated': '立面宽据地图，檐顶据资料约21.6米；各层、花饰和出挑深度用照片比例估计。',
    'coordinate_convention': 'Local GLB +X north, +Y up, +Z east toward the Bund.',
    'interiors_modeled': False, 'source_register': f'source/precise/{ID}/reference-review.json',
    'copyright': 'Original geometry MIT. Bank name uses an OFL subset; no photographs embedded.'
}
if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_riverfront)
