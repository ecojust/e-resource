"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from stone_balcony import PALETTE,add_building
META={'id': 'huangpu-yarn-bank-east-balustraded-balcony', 'name': '上海纱业银行大楼东端弧形石阳台与瓶栏', 'scope': '东端券窗上方外凸的石阳台。两道水平压边围住弧形楼板，瓶栏立在方座上，扶手绕到两端方墩，挑台底下有卷纹石托。', 'model_scope_zh': '东端券窗上方外凸的石阳台。两道水平压边围住弧形楼板，瓶栏立在方座上，扶手绕到两端方墩，挑台底下有卷纹石托。', 'estimated': '节选宽约3.5米，挑出约0.9米。弧面、瓶栏和石托按2013与2021年街摄比例构造。树枝掩住的端部、石雕背面和构件实尺仍待复测。', 'viewer_page': 'yarn-bank-east-balustraded-balcony.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
