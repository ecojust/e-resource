"""Build the photographed curved corner of the American Oriental Bank."""
import argparse
import json
import os
import sys
from pathlib import Path
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from corner_building import add_building as assemble
from street_finish import MATERIALS
from street_services import SERVICE_MATERIALS

ID='huangpu-american-oriental-bank-rounded-corner'
SCOPE='河南中路宁波路弧形转角、两侧各一段直墙，含四层七轴钢窗、入口、砖墩、设备、屋檐与女儿墙。'
META={'id':ID,'name':'上海美丰银行河南中路宁波路弧形转角','viewer_page':'american-oriental-bank-rounded-corner.html',
      'scope':SCOPE,'model_scope_zh':SCOPE,'status':'photo-registered-rounded-street-corner','reference_height_m':15.14,
      'estimated':'街线按OSM足印拟合。窗轴、各层高度、门窗宽度、表面退进及后截面系据街景照片估计。',
      'interiors_modeled':'入口仅保留临街门扇、门槛及浅槽。','coordinate_convention':'Metres. X east along Ningbo Road, Y inward, Z up. The Henan Road tangent continues north.',
      'source_register':'source/precise/'+ID+'/reference-review.json','copyright':'Original geometry and brick artwork: MIT. Shop lettering subset: SIL OFL 1.1. Reference photographs remain at their original sources.'}
PALETTE={**MATERIALS,**SERVICE_MATERIALS}
def add_building(builder,lod):
    assemble(builder,lod,json.loads((SOURCE/'dimensions.json').read_bytes()))

if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['MEIFENG_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
