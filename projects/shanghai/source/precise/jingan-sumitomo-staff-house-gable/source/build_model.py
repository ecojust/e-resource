"""Build the three second-storey windows and timbered gable of 510 Jiaozhou Road."""
from pathlib import Path
import sys
import os
from argparse import ArgumentParser
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from staff_house import PALETTE, add_building
ID='jingan-sumitomo-staff-house-gable'
NAME='司米托莫银行职员宿舍（培进中学6号楼）胶州路侧山墙三联窗'
SCOPE='胶州路510号院中主楼赭红山墙、二层三扇窗、阁窗、浅色木饰与局部瓦檐。'
META={
    'id':ID,'name':NAME,'viewer_page':'sumitomo-staff-house-gable.html',
    'status':'photo-informed-sumitomo-staff-house-gable','model_scope_zh':SCOPE,'scope':SCOPE,
    'estimated':'以2020年两处街景与2024年陈洁正面照片确定山墙和洞口。木框厚度、玻璃进深及瓦口按照片估计。',
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'coordinate_convention':'Metres, Z up. Local X follows the southwest face to the southeast. Positive Y runs inward. The panel begins approximately 4.70m above ground.',
    'copyright':'Original geometry under MIT. Documentary images are credited and not embedded.'
}
if __name__=='__main__':
    parser=ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['SUMITOMO_317_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
