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
from arched_light import ID, PALETTE, add_building, texture

scope='市表5A063列永嘉路17号住宅。依据Antigng在2015年9月9日拍摄的题名原照，取浅墙的大弧窗、叠券、券脚和较窄侧窗。'
META=dict(id=ID,name='永嘉路17号住宅大弧窗与分层券脚',scope=scope,model_scope_zh=scope,viewer_page='yongjia-17-round-headed-window.html',reference_height_m=4.61,all_dimensions_estimated=True,estimated='2015年照片仰拍，绿色多边形构架与树木遮住局部；模型仅复原可连续读取的墙面和拱边。窗内反光、绝对尺度及后期摄影设备遮挡处无独立实测。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
