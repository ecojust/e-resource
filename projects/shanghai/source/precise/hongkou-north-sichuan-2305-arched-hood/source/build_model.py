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
from console import ID, PALETTE, add_building, texture

scope='四川北路2305号署名街照中，半圆门券的两侧各有一枚收脚的曲线托座，上部托起平出门檐，檐底有一排小齿饰。模型取门券起拱线以上及两侧托座。'
META=dict(id=ID,name='四川北路2305号住宅弧券门头与双曲托',scope=scope,model_scope_zh=scope,viewer_page='north-sichuan-2305-arched-hood.html',reference_height_m=2.46,all_dimensions_estimated=True,estimated='拍摄方向贴近街沿，近处托座比远处大。现行名录覆盖邻近多弄及门牌，只有2305号作为本件原照所题地址。曲托的进深及左端被遮去的轮廓据右端估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
