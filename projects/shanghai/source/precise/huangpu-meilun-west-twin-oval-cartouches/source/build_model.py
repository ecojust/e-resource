"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from corner_cartouches import PALETTE,add_building
META={'id': 'huangpu-meilun-west-twin-oval-cartouches', 'name': '美伦大楼西楼转角柱头双面椭圆盾饰', 'scope': '西楼转角斜面与侧面相接的一根石柱，柱首两面各有一枚椭圆盾饰，盾面有珠花，周缘的卷叶向上翻回，顶部和底部又收成短叶。柱身的凹缝与上方线脚继续绕角。', 'model_scope_zh': '西楼转角斜面与侧面相接的一根石柱，柱首两面各有一枚椭圆盾饰，盾面有珠花，周缘的卷叶向上翻回，顶部和底部又收成短叶。柱身的凹缝与上方线脚继续绕角。', 'estimated': '两面节选各宽约0.57米，柱头连下方两层石皮约高0.88米。双盾、边叶及整体比例按实名历史照片与街摄估建，浅浮雕背面、石种与实际高程待测。', 'viewer_page': 'meilun-west-twin-oval-cartouches.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
