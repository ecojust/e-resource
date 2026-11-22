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
from brick_windows import ID, PALETTE, add_building, texture

scope='Antigng于2018年2月7日摄下中信一村红砖街墙。两樘并排的深色双扇窗共用一条浅色水平檐线。每个窗头的两端弯收至细边框，窗底则各自伸出一块浅色阶形窗台。'
META=dict(id=ID,name='中信一村沿街双窗的连檐、曲肩与双层窗台',scope=scope,model_scope_zh=scope,viewer_page='zhongxin-yicun-twin-window-lintels.html',reference_height_m=2.07,all_dimensions_estimated=True,estimated='市表5D110把延庆路80、82、84号并列。摄影页面文件名为“延庆路82号住宅”，作者图像说明为“延庆路80号住宅”；本件以这排住宅的登记名称识别画中相邻双窗。护栏、电线和两侧树遮住部分窗面，窗框进深和挑出尺寸依可见边缘估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
