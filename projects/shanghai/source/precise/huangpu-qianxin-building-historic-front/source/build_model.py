"""Rebuild a standalone elevation detail from the dated 2015 Qianxin photograph."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from arcade import PALETTE,add_building

ID='huangpu-qianxin-building-historic-front'
SCOPE='按2015年2月17日公开照片制作江西中路中央两排三券窗廊、红砖拱腹、窗扇、下排三处石栏和短檐带。'
META={
    'id':ID,'name':'谦信大楼江西中路中央六券窗廊',
    'viewer_page':'qianxin-six-arches-history.html',
    'status':'historical-photo-informed-facade-study','model_scope_zh':SCOPE,'scope':SCOPE,
    'reference_height_m':7.99,
    'estimated':'片段高约7.99米、宽约9.68米。取自画面比例，用于描述建筑构件，原建筑精确尺度待考。',
    'coordinate_convention':'Standalone architectural fragment in metres, Z up. The front faces negative Y.',
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'copyright':'Original MIT architecture meshes and material colours. The documentary photograph is cited separately.'
}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['QIANXIN_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
