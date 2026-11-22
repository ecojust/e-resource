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
from stepped_wall import ID, PALETTE, add_building, texture

scope='Fayhoo于2015年5月9日拍到高桥蔡宅封火山墙。端头随墙身分级增高，白色窄端层层叠出，三角形小面内有浅浮弧纹；上方的深色瓦盖和脊尖向上翘起。'
META=dict(id=ID,name='高桥蔡宅阶梯封火山墙的两级瓦头与三角灰饰',scope=scope,model_scope_zh=scope,viewer_page='cai-residence-stepped-tiled-wall.html',reference_height_m=2.65,all_dimensions_estimated=True,estimated='市表为季景北路714弄11号，照片另列北街104弄11号。摘取能在原照区分的相邻两级；墙端饰纹细小，浅浮弧纹、压瓦搭接、背面和绝对尺度按可见比例估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
