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
from steel_bays import ID, PALETTE, add_building, texture

scope='第五批市表登记福州路37号为美商卫利韩公司。取Fayhoo在2015年9月3日高处拍下的长立面右部顶层和下一层两开间。'
META=dict(id=ID,name='美商卫利韩公司楼顶层双列窄窗与宽钢窗',scope=scope,model_scope_zh=scope,viewer_page='fuzhou-37-upper-steel-windows.html',reference_height_m=5.25,all_dimensions_estimated=True,estimated='现场照片从邻近高处斜看，平面方向、各扇开启角、窗台进深和绝对尺度另待实测。屋顶棚架、空调和近侧相邻红瓦屋未收入局部。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
