"""Rebuild the documented rounded Fuzhou Road corner of the former Zhongxing Bank."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from curved_front import PALETTE,add_building

ID='huangpu-zhongxing-bank-curved-front'
META={'id': 'huangpu-zhongxing-bank-curved-front', 'name': '中兴银行前楼（福州路与四川中路圆弧窗墙）', 'viewer_page': 'zhongxing-bank-curved-front.html', 'scope': '六层前楼东北圆弧窗墙的三条窗轴、窗下浅凹板与托臂挑檐。', 'model_scope_zh': '福州路89号的六层L形前楼，圆弧处自基座至顶层。两侧直街墙、独立后楼和连接体另行研究。', 'status': 'original-photo-informed-exterior', 'reference_height_m': 21.66, 'estimated': '圆弧据OSM五个节点拟合，弧长13.05米。层高、进退、石材或抹灰颜色按2015年街照比例近似，两对照图不替代实测。', 'coordinate_convention': 'Right-handed local metres. Origin is the midpoint of the photographed street arc. +X toward Fuzhou Road, +Y southwest into the building, +Z up.', 'source_register': 'source/precise/huangpu-zhongxing-bank-curved-front/reference-review.json', 'interiors_modeled': False, 'copyright': 'Original exterior geometry and original synthesized mineral-grain texture. Photographs cited as reference.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['ZHONGXING_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
