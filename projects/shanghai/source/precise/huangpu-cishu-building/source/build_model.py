"""Rebuild the street corner of the Continental Mercantile Building in Shanghai."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from street_corner import PALETTE, add_geometry

ID = 'huangpu-cishu-building'
SCOPE = ('南京东路353号慈淑大楼东北角。七层街墙含东北斜角、南京东路侧四组与山东中路侧三组'
         '近角窗跨、沿街店面、退台塔身与顶部环架。两条街的远端、九江路侧、主楼其余屋面和商场内通道待核。')
META = {'id': ID, 'name': '慈淑大楼（东北街角及塔亭）', 'viewer_page': 'cishu-building.html',
        'status': 'original-photo-informed-exterior', 'scope': SCOPE, 'model_scope_zh': SCOPE,
        'estimated': SCOPE, 'interiors_modeled': False, 'source_register': f'source/precise/{ID}/reference-review.json',
        'coordinate_convention': 'Metres. X from Shandong Road toward East Nanjing Road across the chamfer, Y inward, Z up.',
        'copyright': 'Original geometry and materials, MIT.'}
if __name__ == '__main__':
    build(SOURCE, META, PALETTE, add_geometry)
