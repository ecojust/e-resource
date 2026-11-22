"""Build the stone portal and gabled central bay photographed at 601 Jiaozhou Road."""
from pathlib import Path
import sys
import os
from argparse import ArgumentParser
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from school_entrance import PALETTE, add_building
ID='jingan-science-hall-school-arched-entrance'
NAME='上海市科学馆（市立实验民众学校旧址）1号楼石券门与山墙小阳台'
SCOPE='胶州路601号院内1号楼中央的三层连续窗带、嵌套石券门、铁栏小阳台和红砖尖山墙。'
META={
    'id':ID,'name':NAME,'viewer_page':'science-hall-school-arched-entrance.html',
    'status':'photo-informed-science-hall-school-arched-entrance','model_scope_zh':SCOPE,'scope':SCOPE,
    'estimated':'以2015年正照、2021年两处街景交会和2024年院内近照确定山墙、窗带及石券。门扇遮光面、券环的进深和栏杆厚度按照片估计。',
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'coordinate_convention':'Metres, Z up. Local X follows the road-facing school wall from OSM vertices 12 to 13. Positive Y runs inward. The base is at courtyard level.',
    'copyright':'Original geometry under MIT. Documentary images are credited and not embedded.'
}
if __name__=='__main__':
    parser=ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['SCIENCE_HALL_320_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
