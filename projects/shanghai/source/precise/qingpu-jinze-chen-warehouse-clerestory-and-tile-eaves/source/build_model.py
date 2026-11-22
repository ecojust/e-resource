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
from warehouse_eaves import ID, PALETTE, add_building, texture

scope='金泽镇下塘街16号为陈家仓库。Fayhoo署名街照显示，长白墙上有连续的暗色瓦头，靠后较高的瓦檐下露出狭长的分格窗带。取照片中墙顶和后方屋檐同时清楚的一段，建两道青灰瓦檐、两者之间的暗色竖框及下部抹灰线。'
META=dict(id=ID,name='金泽陈家仓库层檐之间的窄窗带与小青瓦',scope=scope,model_scope_zh=scope,viewer_page='jinze-chen-warehouse-clerestory-and-tile-eaves.html',reference_height_m=2.07,all_dimensions_estimated=True,estimated='原照题注为下塘街16至17号，市表所列为16号。该照片可指认陈家仓库临街立面，未给整段墙内的分户边界。窗格内侧和各道瓦的进深、瓦形半径与绝对尺寸按单幅街照估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
