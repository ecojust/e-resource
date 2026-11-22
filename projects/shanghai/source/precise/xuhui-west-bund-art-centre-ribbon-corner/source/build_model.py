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
from steel_ribbon import ID, PALETTE, add_building, texture

scope='Fayhoo在2015年3月29日拍摄的龙腾大道2555号西岸艺术中心照片中，浅灰体量一侧的两排钢窗由实墙分成开间，绕过实体转角，另一侧接成两道长窗。屋顶轮廓上方另立窄条绿色采光窗。'
META=dict(id=ID,name='西岸艺术中心转角的两层钢格带窗与屋面采光窗',scope=scope,model_scope_zh=scope,viewer_page='west-bund-art-centre-ribbon-corner.html',reference_height_m=2.6,all_dimensions_estimated=True,estimated='本件选照片中与白色外墙相连的局部。玻璃进深与屋顶灰色端头的倾角由单张照片估计，后方高厅、底部票房与红棚以及建筑改造各年代不作推定。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
