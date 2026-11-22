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
from double_face import ID, PALETTE, add_building, texture

scope='2018年2月的街照可见转角两面均有黑色方格窗。靠左的一面在窗下有一排直杆，转角右侧短面的窗套为浅灰色，其下栏心留有四段曲线围成的菱花。'
META=dict(id=ID,name='愚园路1039号住宅转角钢格窗与下槛铁花',scope=scope,model_scope_zh=scope,viewer_page='yuyuan-1039-steel-corner-windows.html',reference_height_m=2.65,all_dimensions_estimated=True,estimated='所建范围为连续楼窗中最靠前的一角。立面开间、窗腔和窗下铁栏的深度按透视比例近似；原照片没有施工年代和测绘尺寸。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
