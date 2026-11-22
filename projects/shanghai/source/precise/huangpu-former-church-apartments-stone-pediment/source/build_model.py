"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from stone_pediment import PALETTE,add_building
META={'id': 'huangpu-former-church-apartments-stone-pediment', 'name': '原教会公寓南苏州路入口石三角山花', 'scope': '79号公寓入口门上的三角形石山花。层叠的两道斜向石线在中央合拢，山花墙心分层砌筑；水平底线在两边门柱上方折出，底下接石门楣与柱头。', 'model_scope_zh': '79号公寓入口门上的三角形石山花。层叠的两道斜向石线在中央合拢，山花墙心分层砌筑；水平底线在两边门柱上方折出，底下接石门楣与柱头。', 'estimated': '门罩节选估宽约3.4米，三角山花估高0.95米。比例来自正面和斜面街摄，石材品种、背面深度和绝对尺寸待现场实测。', 'viewer_page': 'former-church-apartments-stone-pediment.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
