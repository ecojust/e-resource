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
from faceted_stair import ID, PALETTE, add_building, texture

scope='市表永福路68号、复兴西路91及93号良友公寓。上海房管的俯照、扶手侧照和台阶特写显示不规则折边的楼梯井、赭红木扶手、黑色细栏杆和马赛克踏面。据此截取一层连续的梯段与转折平台。'
META=dict(id=ID,name='良友公寓多边形楼梯井与折角木扶手',scope=scope,model_scope_zh=scope,viewer_page='liangyou-angular-three-flight-stair.html',reference_height_m=4.27,all_dimensions_estimated=True,estimated='俯拍存在透视收缩，模型的井宽、坡度、每跑级数以及楼板厚度按可见比例估算。公共墙面、其他两部楼梯和上层重复部分超出此次截取范围。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
