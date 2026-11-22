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
from balconies import ID, PALETTE, add_building, texture

scope='按Fayhoo在2014年12月9日从街口拍摄的照片，重现南昌路107号三层斜切墙面两座分开的挑台、成对石托、深色细铁栏和各自的玻璃门。'
META=dict(id=ID,name='南昌路107号住宅三层双挑台与铁栏',scope=scope,model_scope_zh=scope,viewer_page='nanchang-107-twin-cantilever-balconies.html',reference_height_m=3.87,all_dimensions_estimated=True,estimated='门牌与建筑有摄影者题注；绝对高度、挑台进深、细杆数量和室内窗背均无实测。两端仅截取转角短段。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
