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
from brick_chimney import ID, PALETTE, add_building, texture

scope='市表并列180、182号。2018年署名180号住宅的原照片显示，临街红砖山墙中央有一宽矩形烟囱高出两条深色斜封檐；两边的窄白框阁窗与烟囱位于同一端面。'
META=dict(id=ID,name='乌鲁木齐南路180号住宅山墙烟囱与阁楼双窗',scope=scope,model_scope_zh=scope,viewer_page='wulumuqi-180-gable-chimney-and-lights.html',reference_height_m=3.29,all_dimensions_estimated=True,estimated='房屋局部有枝干与电缆遮住，截取可追踪的烟囱顶部、山墙斜边和两侧白框。未独立认定182号的部件。背面、烟道内腔、墙厚与屋面进深缺乏实测，截面尺度按照片比例。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
