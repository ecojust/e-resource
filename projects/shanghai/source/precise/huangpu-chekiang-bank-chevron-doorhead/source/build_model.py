"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from bronze_doorhead import PALETTE,add_building
META={'id': 'huangpu-chekiang-bank-chevron-doorhead', 'name': '浙江实业银行大楼福州路入口折线门楣与串珠', 'scope': '107号矩形门洞的深色金属门楣，中央三层向下叠合的人字折线，下方见斜面，两边各有带圆饰与串珠的阶形垂板。', 'model_scope_zh': '107号矩形门洞的深色金属门楣，中央三层向下叠合的人字折线，下方见斜面，两边各有带圆饰与串珠的阶形垂板。', 'estimated': '节选宽约2.44米，金属板宽约1.82米。前脸比例来自2017与2020年相同门牌的街摄；材质以照片中的暗褐金属表现，原有合金、厚度与背面尚待实测。', 'viewer_page': 'chekiang-bank-chevron-doorhead.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
