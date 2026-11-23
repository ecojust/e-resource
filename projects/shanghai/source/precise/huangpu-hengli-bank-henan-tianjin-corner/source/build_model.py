"""Build the present Tianjin Road and Middle Henan Road fronts of Hengli Bank."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from bank_fronts import PALETTE,add_building

ID='huangpu-hengli-bank-henan-tianjin-corner'
SCOPE='河南中路、天津路西北隅恒利银行的棕砖斜门、两街窗墙、可见退台和立面设备，依2020至2021现状。'
META=dict(id=ID,name='恒利银行河南中路天津路转角入口与竖窗立面',viewer_page='hengli-bank-henan-tianjin-corner.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-street-elevations',source_register=f'source/precise/{ID}/reference-review.json',estimated='三段街墙按冻结底图为15.82、4.36与29.21米。相片与三台道路全景估得斜角低檐约19.35米、最高可见退台约29.2米。材料厚度、挑檐及屋顶轮廓进深含估计。',coordinate_convention='Metres. Local X along Tianjin Road toward the corner. Y points into the bank. Origin is the south end of the corner chamfer.',interiors_modeled=False,copyright='Original MIT geometry and procedural brickwork. Letter glyphs from a Noto Sans CJK SC subset under SIL OFL 1.1. Research photos are separately credited.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    options,rest=parser.parse_known_args()
    os.environ['HENGLI_BLENDER']=options.blender
    sys.argv[1:]=[*rest,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
