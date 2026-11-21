"""Build the historic garden elevation seen in the reprinted Qu Kai photograph."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE))
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from garden_facade import MAT as PALETTE,add_building

ID='huangpu-ruikang-comprador-residence'
SCOPE='依据瞿凯拆除前旧影的2019再刊稿、相反方向旧影和街坊图，制作贝润生旧宅朝庭院的五段红砖立面、叠券廊、山花及短侧返。'
META={
    'id':ID,'name':'瑞康洋行买办住宅（贝润生宅）历史庭院立面',
    'viewer_page':'ruikang-comprador-residence-history.html',
    'status':'historical-photo-informed-facade-study','model_scope_zh':SCOPE,'scope':SCOPE,
    'reference_height_m':16.59,
    'estimated':'旧航片街坊配准给出屋面宽约30米。各楼层及檐高按照片估计；建筑原图、后部及庭院待查。',
    'coordinate_convention':'Standalone architectural fragment in metres, Z up. The front faces negative Y.',
    'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
    'copyright':'Original MIT architecture meshes and material colours. The documentary photograph is cited separately.'
}
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,remainder=parser.parse_known_args()
    os.environ['RUIKANG_BLENDER']=options.blender
    sys.argv[1:]=[*remainder,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
