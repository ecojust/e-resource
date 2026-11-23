"""Package the documented Art Deco east street wall at 473 Middle Jiangxi Road."""
import argparse
import os
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from bank_front import PALETTE,add_building
ID='huangpu-yuanyuanchang-bank-jiangxi-front'
SCOPE='源源长银行江西中路473号的两层棕砖东立面、双壁柱、横翼圆徽、退台及门窗。照片可见的门扇和卷门按其外形简化；其余立面与原始门窗档案另查。'
META=dict(id=ID,name='源源长银行江西中路473号圆徽砖立面',viewer_page='yuanyuanchang-bank-jiangxi-front.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-street-facade',source_register=f'source/precise/{ID}/reference-review.json',estimated='19.05米宽度来自原城东边界。两条街道的公共全景交叉定位，屋顶线、开间和构件深度按照片估算。',coordinate_convention='Metres, +X north along Jiangxi Middle Road, +Y inland, +Z up.',interiors_modeled=False,copyright='Original MIT geometry and procedural firebrick atlas. Source photography credited separately.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,other=parser.parse_known_args()
    os.environ['YUANYUANCHANG_BLENDER']=options.blender
    sys.argv[1:]=[*other,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
