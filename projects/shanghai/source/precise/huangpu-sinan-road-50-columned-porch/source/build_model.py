"""Build the photographed hipped-roof entrance porch at 50 Sinan Road."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from sinan_porch import PALETTE, add_building

ID='huangpu-sinan-road-50-columned-porch'
NAME='思南路50号花园住宅瓦檐门廊'
SCOPE='思南路50号靠思南路的瓦檐入口，包括四坡小瓦顶、一根独立圆柱、与实墙相接的过梁、石阶、门扇与50号门牌。'
META={
    'id':ID,'name':NAME,'viewer_page':'sinan-road-50-columned-porch.html',
    'status':'photo-informed-sinan-road-residence-porch','model_scope_zh':SCOPE,'scope':SCOPE,
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'coordinate_convention':'Metres, Z up; X points north along the eastern street wall, Y points inward beneath the porch. The outer stone stair meets the paving at Z=0.',
    'estimated':'2017年斜照确认一根独立圆柱与墙端过梁，2020年门牌可读50。2021年1月两个街景站交会标定柱脚、檐与屋脊。门后格扇、屋瓦排数与四级石阶的中段取照片近似值。',
    'copyright':'Original architectural geometry, materials and drawn numerals under MIT. Documentary photographs are credited and are not embedded.'
}
if __name__=='__main__':
    options,remaining=ArgumentParser(add_help=False),None
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['SINAN_342_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
