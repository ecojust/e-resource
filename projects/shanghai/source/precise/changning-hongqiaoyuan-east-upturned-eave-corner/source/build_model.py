"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from upturned_eaves import PALETTE,add_building
META={'id': 'changning-hongqiaoyuan-east-upturned-eave-corner', 'name': '虹桥源一号东楼歇山顶翘角与瓦垄', 'scope': '恢复东楼歇山檐角的一段，两向灰瓦在斜角脊下咬合，棕木檐板随屋角起翘，两边檐下可见逐根排开的短椽头。', 'model_scope_zh': '恢复东楼歇山檐角的一段，两向灰瓦在斜角脊下咬合，棕木檐板随屋角起翘，两边檐下可见逐根排开的短椽头。', 'estimated': '根据照片估单边檐口取样约1.95米，截取角梁、短椽、两片坡面和其上的阴阳瓦。正脊端饰与西楼立面另行调查。', 'viewer_page': 'hongqiaoyuan-east-upturned-eave-corner.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the principal facade, local Y points inward, Z is up. Units in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
