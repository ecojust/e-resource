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
from hotel_bays import ID, PALETTE, add_building, texture

scope='第五批5A047登记福建南路33号大方饭店。2013年与2015年的同址图可读锦江之星的中英文招牌，2017年和2021年见康铂；取两期均可对照的上层临街双开间窗楣及栏板。'
META=dict(id=ID,name='大方饭店福建南路弧形窗楣与悬挑栏板',scope=scope,model_scope_zh=scope,viewer_page='dafang-hotel-segmental-window-balconies.html',reference_height_m=6.6,all_dimensions_estimated=True,estimated='立面层高、构件厚度和墙体截深依照片比例估算。未定建造年代、墙材配方或改造年份，招牌和临时绿棚另有实照可查。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
