"""Package original site-oriented exterior geometry for No. 1 The Bund."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT / 'tools'))
from package_architectural_model import build
from asia_geometry import PALETTE, add_building

ID = 'huangpu-asia-building'
SCOPE = '参考2011年东南转角、2021年与2025年东立面照片制作现存外观。两面临街七开间、退廊、门廊、凹转角、顶层角亭与中央采光屋面有几何细分。高度、背立面、屋顶和不可见处为估计。'
META = {'id': ID, 'name': '亚细亚大楼（外滩1号双街立面与东南转角）', 'status': 'original-photo-informed-exterior',
        'viewer_page': 'asia-building.html', 'scope': SCOPE, 'model_scope_zh': SCOPE, 'estimated': SCOPE,
        'source_register': 'source/precise/'+ID+'/reference-review.json', 'interiors_modeled': False,
        'coordinate_convention': 'Blender east, north, up in metres. Origin is the frozen Overture footprint centroid. GLB east, up, south.',
        'copyright': 'Original geometry MIT. Reference photographs are not embedded.'}

if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_building)
