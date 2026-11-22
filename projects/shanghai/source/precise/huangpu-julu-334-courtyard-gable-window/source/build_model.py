"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from courtyard_gable import PALETTE,add_building
META={'id': 'huangpu-julu-334-courtyard-gable-window', 'name': '巨鹿路334号院内尖山墙窗与双坡瓦檐', 'scope': '巨鹿路334号院内临街可见的一开间尖山墙。两道红色斜檐在墙顶相交，浅色山面中嵌上窄下高的一组六格窗，窗台下有一段水平腰线。', 'model_scope_zh': '巨鹿路334号院内临街可见的一开间尖山墙。两道红色斜檐在墙顶相交，浅色山面中嵌上窄下高的一组六格窗，窗台下有一段水平腰线。', 'estimated': '2013年与2021年的街景均可见同一尖顶、矩形窗洞与右边廊柱。模型采用2021年浅色粉刷后的外观，按窗宽约1.30米换算可见比例。两站交会角仅约4.3–4.8度，院内楼号、原始建造年代、瓦的背面和进深尚欠实测。', 'viewer_page': 'julu-334-courtyard-gable-window.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
