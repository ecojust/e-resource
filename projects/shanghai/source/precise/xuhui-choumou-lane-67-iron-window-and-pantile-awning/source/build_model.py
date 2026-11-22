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
from iron_window import ID, PALETTE, add_building, texture

scope='淮海中路1857弄67号北入口上方，矩形窗洞中嵌尖拱形铁窗。上部两条弯梃朝中央汇拢，拱肩留卷草铁花，下部双扇外有一排侧砖窗台。窗下向外伸出带重叠筒瓦的雨厦。'
META=dict(id=ID,name='绸缪村67号北入口铁花窗与筒瓦雨厦',scope=scope,model_scope_zh=scope,viewer_page='choumou-lane-67-iron-window-and-pantile-awning.html',reference_height_m=4.64,all_dimensions_estimated=True,estimated='模型表现发表照片里的北入口上部。高参88记原有的铁艺支托筒瓦雨厦已经改建，模型只复现图上的瓦面和前沿。玻璃色彩按照片明暗概括，雨厦背部、固定做法与实际尺寸缺少测绘。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
