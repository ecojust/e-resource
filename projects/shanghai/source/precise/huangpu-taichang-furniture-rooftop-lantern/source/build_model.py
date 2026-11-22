"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from lantern import PALETTE,add_building
META={'id': 'huangpu-taichang-furniture-rooftop-lantern', 'name': '泰昌木器公司转角屋顶亭的穹顶与叠檐', 'scope': '南京东路740号转角的敞亭。低圆穹顶压在数层折线石檐上，街面几根细柱之间留空；柱下的斜台上有浅浅的折面装饰。', 'model_scope_zh': '南京东路740号转角的敞亭。低圆穹顶压在数层折线石檐上，街面几根细柱之间留空；柱下的斜台上有浅浅的折面装饰。', 'estimated': '以2016年具名全幅照片及其屋面局部为几何依据。亭檐估宽约2.1米，曲率、进深及相邻柱距按照片比例近似。店侧街摄只能核门面；背面被遮的柱列、设备和广告牌均未复原。', 'viewer_page': 'taichang-furniture-rooftop-lantern.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
