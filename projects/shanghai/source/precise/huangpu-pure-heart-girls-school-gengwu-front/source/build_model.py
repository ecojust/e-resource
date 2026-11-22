"""Rebuild a standalone elevation detail from the historic Gengwu school elevation."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from front import PALETTE,add_building

ID='huangpu-pure-heart-girls-school-gengwu-front'
SCOPE='依据庚午校舍的民国照片和2014年正面照片，制作中央五开间、双层窗列与四根通高柱、十道菱形饰、阁层五窗和四石键山花圆窗。'
META={
    'id':ID,'name':'清心女中庚午校舍（北大楼）中央山花柱列正面',
    'viewer_page':'pure-heart-girls-school-history.html',
    'status':'historical-photo-informed-facade-study','model_scope_zh':SCOPE,'scope':SCOPE,
    'reference_height_m':14.80,
    'estimated':'片段高约14.80米、宽约19.30米。取自画面比例，用于描述建筑构件，原建筑精确尺度待考。',
    'coordinate_convention':'Standalone architectural fragment in metres, Z up. The front faces negative Y.',
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'copyright':'Original MIT architecture meshes and material colours. The documentary photograph is cited separately.'
}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['GENGWU_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
