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
from window_hoods import ID, PALETTE, add_building, texture

scope='市表5A043登记香港路117号为SHELL汽车公司、美灵登有限公司、永实业有限公司旧址，现名凯恩宾馆。模型取Antigng在2015年7月20日拍到的两种并列窗楣及上部窗间墙。'
META=dict(id=ID,name='香港路117号键石窗楣与三角窗山花',scope=scope,model_scope_zh=scope,viewer_page='hongkong-117-pedimented-windows.html',reference_height_m=5.1,all_dimensions_estimated=True,estimated='仅据可见门面塑造。防护铁栅与现有窗框表现照片年份；浮饰深度、墙体截面与尺寸采用图片比例，未与旧城足印对齐。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
