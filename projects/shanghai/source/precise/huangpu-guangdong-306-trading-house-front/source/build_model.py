"""Rebuild the eight-axis Guangdong Road elevation."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from streetwall import PALETTE,add_building

ID='huangpu-guangdong-306-trading-house-front'
META={'id': 'huangpu-guangdong-306-trading-house-front', 'name': '广东路306号洋行旧址南立面长阳台与几何饰带', 'viewer_page': 'guangdong-306-trading-house-front.html', 'status': 'original-photo-informed-exterior', 'model_scope_zh': '按2014与2020年可核实的沿街正面，制作八个窗轴、中央长阳台、四处箱状小阳台、红色贴面带和折线、菱形几何饰带。底层取2020全景可见门窗分节，不附当期招牌。', 'scope': '按2014与2020年可核实的沿街正面，制作八个窗轴、中央长阳台、四处箱状小阳台、红色贴面带和折线、菱形几何饰带。底层取2020全景可见门窗分节，不附当期招牌。', 'reference_height_m': 16.0, 'estimated': '原房2074的16米为按层数估算；城市原房面积与具名足印重合率98.48%。投影矫正用于比较构件比例，阳台深度与窗洞进深并非测量尺寸。', 'coordinate_convention': 'Local metres. X runs east along Guangdong Road, Y runs into the building, Z up.', 'source_register': 'source/precise/huangpu-guangdong-306-trading-house-front/reference-review.json', 'interiors_modeled': False, 'copyright': 'Original geometry and procedural facing tile based on referenced photographs.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['GUANGDONG306_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
