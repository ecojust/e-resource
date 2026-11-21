"""Build the Donghu Road entrance from the measured canopy, columns and open railing."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from importlib.util import module_from_spec, spec_from_file_location

portico_spec = spec_from_file_location('donghu_entrance_portico', SOURCE / 'portico.py')
portico = module_from_spec(portico_spec)
portico_spec.loader.exec_module(portico)
PALETTE, add_building = portico.PALETTE, portico.add_building
META={'id': 'xuhui-du-residence-donghu-entrance-portico', 'name': '杜氏公馆东湖路70号主楼柱廊雨篷', 'viewer_page': 'du-residence-donghu-portico.html', 'scope': '第四批4D001，东湖路70号。具名OSM 441599775与原城5347吻合，实照可见入口柱廊、雨篷和栏杆。', 'model_scope_zh': '第四批4D001，东湖路70号。具名OSM 441599775与原城5347吻合，实照可见入口柱廊、雨篷和栏杆。', 'copyright': 'Original architectural geometry under MIT. Reference photos credited separately.', 'interiors_modeled': False, 'status': 'photo-informed-open-portico', 'source_register': 'source/precise/xuhui-du-residence-donghu-entrance-portico/reference-review.json', 'estimated': '2020与2021街景交会和2024、2026航片定雨篷轮廓；树影后的栏板重复间隔为约数。', 'coordinate_convention': 'Metres, Z up, X runs along the house front, Y increases from the street towards the house.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
