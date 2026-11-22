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
from blind_arcade import ID, PALETTE, add_building, texture

scope='朱家角天主堂位于漕河街317弄27号。Fayhoo于2016年2月7日从正面记录钟楼。中层两侧红灰相间，中轴两旁排列成对浅凹盲拱，下部各有一道阶梯形菱花，中央另有一枚短横砖。它们与上一层真正敞开的百叶窗分处两段。'
META=dict(id=ID,name='朱家角天主堂钟楼中段双菱形砖花与叠层盲拱',scope=scope,model_scope_zh=scope,viewer_page='zhujiajiao-belfry-brick-lozenges.html',reference_height_m=3.5,all_dimensions_estimated=True,estimated='截取中段正壁至上部挑檐，不延伸至钟室内或旁侧的塑像。灰砖规格、砌体深度、浅凹尺寸与砖色依照片估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
