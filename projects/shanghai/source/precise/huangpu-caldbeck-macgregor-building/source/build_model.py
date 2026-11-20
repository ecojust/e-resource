"""Build the Fuzhou Road historical street wing from the 2014 exterior view."""
from pathlib import Path
import sys
SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from street_wing import PALETTE, add_street_wing

ID = 'huangpu-caldbeck-macgregor-building'
SCOPE = '按2014年福州路44号正面照片及航片可辨红瓦外形制作沿街两层楼翼，含半木构、两座伸出山墙、砖基与坡顶烟囱。后侧白顶建筑与两侧邻楼另列。'
META = {'id': ID, 'name': '正广和公司福州路历史街翼', 'status': 'original-photo-informed-exterior',
        'viewer_page': 'caldbeck-macgregor.html', 'scope': SCOPE, 'estimated': SCOPE, 'model_scope_zh': SCOPE,
        'source_register': f'source/precise/{ID}/reference-review.json', 'interiors_modeled': False,
        'coordinate_convention': 'Author +X photo-right along Fuzhou Road, +Y away from street, Z up. Dimensional estimates.',
        'copyright': 'MIT original geometry and procedural materials. No photo textures.'}

if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_street_wing)
