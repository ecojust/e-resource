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
from arched_door import ID, PALETTE, add_building, texture

scope='Fayhoo于2015年4月12日拍到黄渡路17弄3号临街小门及院门。模型取灰褐色外墙中的拱门，门右有绿色3号牌；可见两道前后错开的红砖券、淡色砖门脚和深色双扇铁门。'
META=dict(id=ID,name='黄渡路17弄3号住宅临街双层砖券门',scope=scope,model_scope_zh=scope,viewer_page='huangdu-lane17-no3-arched-street-door.html',reference_height_m=3.02,all_dimensions_estimated=True,estimated='竖向边界取带3号牌的小门，旁边独立的大铁门及其山墙未做。砖券深度和铁花截面按门旁的透视估算。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
