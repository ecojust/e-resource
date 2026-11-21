"""Build the two street-facing elevations of Shanghai's Savoy Apartments."""
import argparse
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from savoy_front import PALETTE,add_savoy
ID='xuhui-savoy-apartments-street-front'
SCOPE='常熟路、延庆路两翼的四组敞开楼梯、外挑折面窗肚墙、西北转角五层凸窗、浅色檐带、楼顶屋间及底层沿街店面。'
META=dict(id=ID,name='赛华公寓常熟路、延庆路转角立面',viewer_page='savoy-apartments.html',scope=SCOPE,model_scope_zh=SCOPE,
          status='street elevations after the 2020–21 repair',source_register='source/precise/'+ID+'/reference-review.json',
          estimated='常熟路48.03米、延庆路40.40米，二者通过10.06米西北斜角相接。按2016和2021照片估算窗、落地高度、楼梯进深与屋顶间位置。',interiors_modeled=False,
          coordinate_convention='X points southwest along the northwest chamfer, Y into the building and Z up. glTF +Z faces the street junction.',
          copyright='Original modeled surfaces under MIT. The sources are credited separately.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['SAVOY_APARTMENTS_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_savoy)
