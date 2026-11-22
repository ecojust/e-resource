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
from twin_hipped_dormers import ID, PALETTE, add_building, texture

scope='Fayhoo于2017年1月28日从高处拍摄保定路410至448号双号联排住宅。大坡屋面分作多段，取紧邻左侧大山墙右边的两扇老虎窗，各有向前收尖的小坡、两侧瓦面及短脊。'
META=dict(id=ID,name='保定路410至448号住宅成对老虎窗与瓦顶斜脊',scope=scope,model_scope_zh=scope,viewer_page='baoding-road-twin-hipped-dormers.html',reference_height_m=2.01,all_dimensions_estimated=True,estimated='原照片题到整排双号，无法逐窗指定是哪一户。以照片左侧大山墙向右计，取紧邻山墙的下一组双窗；屋面瓦片尺度、窗洞深和屋后不可见处作比例估计，窗外晾衣架与空调未做。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
