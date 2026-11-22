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
from flowered_window import ID, PALETTE, add_building, texture

scope='2018年8月2日Antigng拍摄的《襄阳南路351–355号住宅》中，红砖立面一层可见灰绿色窗框。窗楣有一行六朵小花，两朵花之间伸出带卷尖的对称垂叶。作品取原照里清楚的一段窗头和窗间饰带。'
META=dict(id=ID,name='襄阳南路351至355号街面窗框花饰与垂叶',scope=scope,model_scope_zh=scope,viewer_page='xiangyang-351-355-floral-window-surround.html',reference_height_m=1.72,all_dimensions_estimated=True,estimated='市表5D054列襄阳南路349至355号单号，较早名录简记355号。照片可读的绿色357弄牌挂在前景院门。本作取后方住宅窗饰，现有证据不能进一步指定这扇窗的单独户号。深度和遮挡处只按可见形状估计。')
if __name__=='__main__':
    texture()
    build(source,META,PALETTE,add_building)
