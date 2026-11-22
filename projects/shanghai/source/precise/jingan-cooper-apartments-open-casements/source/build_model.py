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
from eave_and_open_casements import ID, PALETTE, add_building, texture

scope='取Antigng于2017年8月19日从院内拍摄的古柏公寓，表现中段凸出窗间顶层的两扇外开分格窗、浅色粗抹灰墙和外挑瓦檐。'
META=dict(id=ID,name='古柏公寓中段上层外开窗与瓦檐',scope=scope,model_scope_zh=scope,viewer_page='cooper-apartments-open-casements.html',reference_height_m=2.86,all_dimensions_estimated=True,estimated='原照看得到每扇的两道横档和打开后的阴影。两扇开启角、真实木材种类、檐的绝对悬挑与屋面完整坡度均未经测量，窗下后装设备遮住的构造未推定。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
