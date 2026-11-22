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
from court_gallery import ID, PALETTE, add_building, texture

scope='成都北路337号新成大厦的小区资料保留两幅院照。本件截取靠楼梯的一层外廊，橙褐色廊板自侧廊向院心弯出，栏框沿同一边缘转折。'
META=dict(id=ID,name='新成大厦院内弧形外廊与菱格铁栏',scope=scope,model_scope_zh=scope,viewer_page='xincheng-apartments-curved-court-gallery.html',reference_height_m=1.77,all_dimensions_estimated=True,estimated='两幅院照均未署名或标拍摄日期，栏网孔径、廊宽、墙厚和栏高为图上比例估计。院落有多幢建筑，模型只展示两照均可辨的外廊一跨。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
