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
from brick_steel_bay import ID, PALETTE, add_building, texture

scope='取Antigng于2018年2月7日从常熟路拍摄的派司公寓立面，截取相邻两层叠置的矩形钢窗与右侧通高砖墩。'
META=dict(id=ID,name='派司公寓两层钢窗与临街砖墙垛',scope=scope,model_scope_zh=scope,viewer_page='pass-apartments-brick-steel-bay.html',reference_height_m=5.9,all_dimensions_estimated=True,estimated='原照可辨深色窗框、浅色天空反光和玻璃前的分格。玻璃与砖墙的绝对进深未经测量，钢窗分格在遮挡处按相邻可读部分延续；不将这开间指定为1–8号中某一户。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
