"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from rusticated_corner import PALETTE,add_building
META={'id': 'huangpu-zhonghe-cun-no14-channelled-window-pier', 'name': '长乐路272弄14号住宅转角横槽墙墩与木格窗', 'scope': '中和邨14号住宅一处外凸转角。水泥墙墩一道道横槽绕到侧面，旁边木窗的玻璃分为上下格，浅色窗台有数道挑边。', 'model_scope_zh': '中和邨14号住宅一处外凸转角。水泥墙墩一道道横槽绕到侧面，旁边木窗的玻璃分为上下格，浅色窗台有数道挑边。', 'estimated': '参照Antigng于2017年拍摄的署名原照估算可见七道墙身分层、三格木窗及窗台。每一层约高0.39米；槽深、窗扇进深及枝叶后的窗格以可见部分为准。', 'viewer_page': 'zhonghe-cun-no14-channelled-window-pier.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
