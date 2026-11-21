"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from lion_portico import PALETTE,add_building
META={'id': 'xuhui-wuyuan-314-welfare-house-lion-portico', 'name': '五原路314号花园住宅石狮券廊', 'viewer_page': 'wuyuan-welfare-house-lion-portico.html', 'status': 'photo-informed-architectural-component', 'model_scope_zh': '1932年五原路314号院内主楼面花园门廊，含三级弧券、两侧通廊、六角灯桩、内退木门、几何铁窗格和一对石狮。', 'scope': '1932年五原路314号院内主楼面花园门廊，含三级弧券、两侧通廊、六角灯桩、内退木门、几何铁窗格和一对石狮。', 'interiors_modeled': False, 'source_register': 'source/precise/xuhui-wuyuan-314-welfare-house-lion-portico/reference-review.json', 'estimated': '现场照片量取比例，缺少工程图，门户净宽、石狮部位的绝对尺寸和投影深度为估计。', 'coordinate_convention': 'X increases eastward viewed from the garden. Positive Y points through the front arch towards the wooden door. Z is measured from the portico paving.', 'copyright': 'Original geometry and analytic materials, MIT. The reference pictures retain their individual copyrights.'}

if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
