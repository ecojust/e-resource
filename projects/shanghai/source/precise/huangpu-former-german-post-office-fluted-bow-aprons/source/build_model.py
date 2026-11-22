"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from bowed_fluting import PALETTE,add_building
META={'id': 'huangpu-former-german-post-office-fluted-bow-aprons', 'name': '原德国邮局转角弧窗下的竖槽饰板', 'scope': '四川中路与福州路转角的上层圆弧窗下，正面饰板的细竖槽连续排列，侧面一段随弧墙折转。两组饰板之间是平整的墙柱，窗台石沿弧线向外挑出。', 'model_scope_zh': '四川中路与福州路转角的上层圆弧窗下，正面饰板的细竖槽连续排列，侧面一段随弧墙折转。两组饰板之间是平整的墙柱，窗台石沿弧线向外挑出。', 'estimated': '模型选取正面一段及照片左侧可见的一段。中间一段按照片比例估宽1.36米、高0.92米；槽数按可辨亮暗线近似，曲率和槽深未经现场测量。', 'viewer_page': 'former-german-post-office-fluted-bow-aprons.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
