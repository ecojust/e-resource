import os
from pathlib import Path
import sys
source = Path(__file__).resolve().parent
roots = list(source.parents)
if os.environ.get('SHANGHAI_MODEL_TOOLS'):
    roots.insert(0, Path(os.environ['SHANGHAI_MODEL_TOOLS']).parent)
tools = next(parent/'tools' for parent in roots if (parent/'tools/package_architectural_model.py').is_file())
sys.path.insert(0, str(tools))
from package_architectural_model import build
from front_arch import ID, PALETTE, add_building, texture

scope='虹口区舟山路394号住宅的正面二层，四列矩形窗上方留有浅色抹灰弧面，外侧是向前挑出的弧形窗罩。前沿石栏开出六个连续的菱形孔，上下保留矩形透孔。金红卫的正照和斜照均标有门牌；高参88另记院内正面拱窗、底层二柱和鹅卵石贴面。'
META=dict(id=ID,name='舟山路394号住宅二层弧形窗罩与六菱格阳台',scope=scope,model_scope_zh=scope,viewer_page='zhoushan-394-arched-window-and-diamond-balcony.html',reference_height_m=4.2,all_dimensions_estimated=True,estimated='模型只取院内正面的二层窗组、窗罩和阳台前栏。窗台、檐口的前挑和栏板截面按照片比例估计；道路一侧的砖山墙阳台另有形制，未并入本件。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
