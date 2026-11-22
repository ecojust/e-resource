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
from terrace import ID, PALETTE, add_building, texture

scope='万航渡路618号原上海美术电影制片厂本部“小白楼”面向庭院处有弧形露台。模型取上观新闻2026年所刊照片中的外挑台板、四根细圆柱和台上向中间收拢的几何铁栏。'
META=dict(id=ID,name='上美影小白楼庭院弧形露台与四根圆柱',scope=scope,model_scope_zh=scope,viewer_page='animation-studio-white-villa-terrace.html',reference_height_m=4.23,all_dimensions_estimated=True,estimated='文章记录了作者2023年秋天的参访，照片没有单列拍摄日及摄影者。廊深、楼板厚和栏杆截面据照片比例估算，园区中其他楼房及近年展陈均不在取景范围。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
