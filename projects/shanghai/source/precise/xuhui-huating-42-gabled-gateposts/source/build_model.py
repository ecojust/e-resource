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
from tiled_posts import ID, PALETTE, add_building, texture

scope='2018年2月7日Antigng拍摄的华亭路42号住宅街门有三座浅灰框、淡黄心的尖顶门柱，左柱挂绿色42号牌。两段黑铁栏一繁一简，本展取三柱与相接的铁栏。'
META=dict(id=ID,name='华亭路42号三座瓦顶门柱与铁栏',scope=scope,model_scope_zh=scope,viewer_page='huating-42-gabled-gateposts.html',reference_height_m=2.328,all_dimensions_estimated=True,estimated='5D046同时登记多处门牌，本展对应原照可读的42号。柱侧、瓦片搭接长度及铁栏后向尺寸为估计。左段卷草的部分轮廓被树叶遮挡，未补作完整铁门的内部扣件。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
