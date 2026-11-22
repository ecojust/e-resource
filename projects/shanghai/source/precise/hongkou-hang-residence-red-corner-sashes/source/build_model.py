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
from corner_sashes import ID, PALETTE, add_building, texture

scope='杭氏住宅后来作舟山路幼儿园。Fayhoo摄于2014年11月23日的舟山路455号照片中，上层窗面在街角折回；一道粗红横档沿两面延续，横档以下的窗格有较细的竖梃，窗脚由浅色石台联结。'
META=dict(id=ID,name='杭氏住宅舟山路455号上层转角红框窗',scope=scope,model_scope_zh=scope,viewer_page='hang-residence-red-corner-sashes.html',reference_height_m=2.15,all_dimensions_estimated=True,estimated='仅按照片中未被藤蔓遮住的上层窗复原。窗框涂层的成分、窗后使用情况及墙厚没有实测数据，窗台进深与角度按原照估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
