"""Generate the open street entrance and the west plaque wall of Qinyuan Cun on Xinzha Road."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from details import PALETTE
from ironwork import rails,posts,east_leaf
from memorial_wall import wall
from surface_finish import apply

ID='jingan-qinyuan-lane-entrance'
SCOPE=('新闸路1124弄沁园邨总弄口，取两道带深度的花铁拱、笼式铁柱、'
       '开启的东侧门扇、悬木匾及西侧三块铭牌所在的一段矮墙。沿街住宅、弄内9号、门房和另外的西门各自保留。')
META={'id':ID,'name':'沁园邨新闸路总弄铁艺拱门与西侧铭牌墙','viewer_page':'qinyuan-lane-entrance.html',
      'scope':SCOPE,'model_scope_zh':SCOPE,'status':'photo-measured partial historic street entrance',
      'source_register':f'source/precise/{ID}/reference-review.json','interiors_modeled':False,
      'estimated':'柱中心距按两站街景交会约3.94米，约±0.5米。拱高、进深、开启角与铁材截面按图估算。',
      'coordinate_convention':'Local X east along the street, Y inward through the gateway, Z up.'}

def add_geometry(builder,lod):
    wall(builder,lod)
    posts(builder,lod)
    rails(builder,lod)
    east_leaf(builder,lod)
    apply(builder)

if __name__=='__main__':
    import argparse,os
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    paths,remaining=parser.parse_known_args()
    os.environ['QINYUAN_BLENDER']=paths.blender
    sys.argv[1:]=[*remaining,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_geometry)
