from pathlib import Path
import sys
import os
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from corner import PALETTE,facade
META={
    'id':'huangpu-gibb-livingston-corner','name':'仁记洋行大楼东南转角与相连街墙',
    'viewer_page':'gibb-livingston-corner.html','status':'original-photo-informed-exterior',
    'scope':'东南圆角三层窗墙和上部鼓座、弧形阳台、贴柱及沿两条街的短墙段。',
    'model_scope_zh':'以2007年、2017年可定位的街角照片制作转角与相连街墙。',
    'estimated':'采用实名地块的街线和圆角半径。窗宽、檐高、柱式细部与材色依据照片估计。',
    'source_register':'source/precise/huangpu-gibb-livingston-corner/reference-review.json',
    'interiors_modeled':False,'coordinate_convention':'X follows Dianchi Road eastward, Y into the block, Z upward, metres.',
    'copyright':'Original geometry and procedural materials, MIT.'}
if __name__=='__main__':
    if '--blender' in sys.argv:
        index=sys.argv.index('--blender')+1
        os.environ['GIBB_CORNER_BLENDER']=sys.argv[index]
        sys.argv[index]=str(HERE/'blender-corner.py')
    else:
        sys.argv.extend(['--blender',str(HERE/'blender-corner.py')])
    build(HERE,META,PALETTE,facade)
