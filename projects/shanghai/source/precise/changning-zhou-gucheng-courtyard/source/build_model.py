"""Package the 2014 courtyard elevation of Lane 115, No. 6."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from courtyard_geometry import PALETTE, add_geometry

ID = 'changning-zhou-gucheng-courtyard'
SCOPE = '泰安路115弄6号朝庭院的入口立面，以2014年署有门牌的实照为据。含门阶、筒瓦雨篷、两层窗洞、铁栏小阳台与局部檐口。后部屋顶、其他立面、室内、低层附屋及相邻住宅另计。'
META = {'id': ID, 'name': '泰安路115弄6号周谷城旧居（庭院入口立面）',
        'status': 'original-photo-informed-exterior', 'viewer_page': 'zhou-gucheng-courtyard.html',
        'scope': SCOPE, 'model_scope_zh': SCOPE, 'estimated': SCOPE, 'interiors_modeled': False,
        'source_register': f'source/precise/{ID}/reference-review.json',
        'coordinate_convention': 'X increases toward the photographed right (WSW), Y inward, Z up. GLB maps XYZ to X,Z,-Y.',
        'copyright': 'Original geometry and procedural materials MIT. No photographic pixels embedded.'}

if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_geometry)
