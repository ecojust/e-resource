"""Build Sun Ke Villa's detached main residence from the documented north and south elevations."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT / 'tools'))
from package_architectural_model import build
from villa_geometry import PALETTE, add_geometry

ID = 'changning-sun-ke-villa'
SCOPE = '孙科别墅主楼，含南花园三尖拱敞廊、东南圆弧开间、阁楼和北侧车廊。屋面和构件尺寸参照影像估计；附楼、门卫室、花园和室内另计。'
META = {'id': ID, 'name': '孙科别墅主楼（南花园敞廊与北门廊）',
        'status': 'original-photo-informed-exterior', 'viewer_page': 'sun-ke-villa.html',
        'scope': SCOPE, 'model_scope_zh': SCOPE, 'estimated': SCOPE, 'interiors_modeled': False,
        'source_register': f'source/precise/{ID}/reference-review.json',
        'coordinate_convention': 'X points east (garden elevation right), Y points north, Z up. GLB maps XYZ to X,Z,-Y.',
        'copyright': 'Original geometry and procedural materials MIT. No third-party image pixels embedded.'}
if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_geometry)
