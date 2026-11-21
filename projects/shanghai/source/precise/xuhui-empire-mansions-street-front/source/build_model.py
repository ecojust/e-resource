"""Build the two street-facing elevations of Shanghai's Empire Mansions."""
import argparse
import os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from empire_front import PALETTE,add_empire
ID='xuhui-empire-mansions-street-front'
SCOPE='淮海大楼修缮后的临街折面、1326号凹入正门、越顶装饰肋、钢窗带、圆窗及底层沿街商铺开口。'
META=dict(id=ID,name='皇家公寓淮海中路、常熟路转角立面',viewer_page='empire-mansions.html',scope=SCOPE,model_scope_zh=SCOPE,
          status='street-exterior-after-2020-restoration',source_register='source/precise/'+ID+'/reference-review.json',
          estimated='淮海中路与常熟路两面分别约61.83、76.49米，沿5455的临街边线。窗带、层高、凸窗进深和街铺间距据照片估算。',interiors_modeled=False,
          coordinate_convention='X points along the east side of the chamfer, Y into the building and Z up. glTF +Z faces the street junction.',
          copyright='Original modeled surfaces under MIT. The sources are credited separately.')
if __name__=='__main__':
    options=argparse.ArgumentParser(add_help=False)
    options.add_argument('--blender',default='blender')
    args,remaining=options.parse_known_args()
    os.environ['EMPIRE_MANSIONS_BLENDER']=args.blender
    sys.argv[1:]=[*remaining,'--blender',str(HERE/'blender_preview.py')]
    build(HERE,META,PALETTE,add_empire)
