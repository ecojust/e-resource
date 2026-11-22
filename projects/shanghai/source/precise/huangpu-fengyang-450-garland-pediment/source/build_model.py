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
from garland_pediment import ID, PALETTE, add_building, texture

scope='取凤阳路450号小楼正面左侧凸部阳台上方的半圆山花、双涡卷及绶带浮饰。2017年5月21日，Fayhoo从院门方向拍到两座同类侧部与较低的中央屋檐。'
META=dict(id=ID,name='凤阳路450号小楼半圆山花与绶带花环',scope=scope,model_scope_zh=scope,viewer_page='fengyang-450-garland-pediment.html',reference_height_m=3.37,all_dimensions_estimated=True,estimated='尺度和浮饰前伸依单张斜向仰拍估计。电线遮挡的小段按两端连续走向连接，花环两侧束结只保留照片上可辨的外轮廓。来源未标方位和具体修缮时间。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
