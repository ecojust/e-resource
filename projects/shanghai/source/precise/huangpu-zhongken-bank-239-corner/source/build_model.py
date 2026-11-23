"""Build the evidenced entrance and tower at 239 East Beijing Road."""
from pathlib import Path
import argparse
import os
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from corner_tower import PALETTE,add_building

ID='huangpu-zhongken-bank-239-corner'
SCOPE='中垦大楼北京东路239号东北斜面门楼、黑铁双扇与上亮、九排三联窗带及退阶塔冠。门楣保留可见的旧字底板，现照难逐字辨认。'
META=dict(id=ID,name='中垦大楼北京东路239号东北转角门楼',viewer_page='zhongken-bank-239-corner.html',scope=SCOPE,model_scope_zh=SCOPE,status='photo-informed-corner-frontage',source_register=f'source/precise/{ID}/reference-review.json',estimated='原城斜边宽7.10米。五站街摄估得门洞宽4.23米，塔冠高约44.7米；位置、高程与进深含估计。',coordinate_convention='Metres. +X along the 239 entrance facing west-northwest, +Y toward the retained block, +Z up.',interiors_modeled=False,copyright='Original MIT geometry. Photographic references are separately credited.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender',default='blender')
    opts,extra=parser.parse_known_args()
    os.environ['ZHONGKEN_BLENDER']=opts.blender
    sys.argv[1:]=[*extra,'--blender',str(SOURCE/'blender_preview.py')]
    build(SOURCE,META,PALETTE,add_building)
