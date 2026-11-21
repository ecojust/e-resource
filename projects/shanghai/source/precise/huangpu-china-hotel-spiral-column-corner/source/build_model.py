"""Rebuild the southwest spiral-column chamfer of the China Hotel at Ningbo and Guizhou Roads."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from hotel import PALETTE,add_building

ID='huangpu-china-hotel-spiral-column-corner'
META={'id': 'huangpu-china-hotel-spiral-column-corner', 'name': '中国大饭店西南切角螺旋柱窗墙', 'viewer_page': 'china-hotel-spiral-corner.html', 'scope': '贵州路、宁波路相交处的西南切角，一轴上窗、两根螺旋石柱、内退入口与两侧各一组邻窗。', 'model_scope_zh': '按2026年署名街照制作门套与窗墙，2015年竖牌与底层商业招牌留史料。', 'status': 'original-photo-informed-exterior', 'reference_height_m': 17.25, 'estimated': '切角宽按具名地块的4.94米边界；分层依据街面比例估算，原楼后部较高体量保留。', 'coordinate_convention': 'Local metres, +X to the southeast along the street chamfer, +Y into the building, +Z up.', 'source_register': 'source/precise/huangpu-china-hotel-spiral-column-corner/reference-review.json', 'interiors_modeled': False, 'copyright': 'Original procedural masonry, carved surfaces and geometry from cited street photographs.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['CHINA_HOTEL_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
