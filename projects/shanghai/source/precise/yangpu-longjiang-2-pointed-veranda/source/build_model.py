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
from veranda import ID, PALETTE, add_building, texture

scope='2015年署名照片中，两段宽玻璃窗之间的短墙开有三扇狭长折线顶窗。模型取这段短墙和正上方的一截瓶式栏杆。'
META=dict(id=ID,name='龙江路2号住宅廊侧三联折线窗与瓶栏',scope=scope,model_scope_zh=scope,viewer_page='longjiang-2-pointed-veranda.html',reference_height_m=3.32,all_dimensions_estimated=True,estimated='依据单张斜照校比例。窗洞进深与栏杆背面均为估算，名录将此处列为院内1号楼，照片没有提供完整建筑尺寸。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
