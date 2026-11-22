"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from window_band import PALETTE,add_building
META={'id': 'yangpu-pingliang-629-upper-window-band', 'name': '平凉路629号临街二层钢窗与绿色檐饰', 'scope': '根据2021年2月的现场影像，复原629号门牌点所在连续立面的三间二层钢窗，逐扇分出六列、三排玻璃及近看可见的下排帘面。上方的棕色封檐托住一道连续的绿色起伏饰带。', 'model_scope_zh': '根据2021年2月的现场影像，复原629号门牌点所在连续立面的三间二层钢窗，逐扇分出六列、三排玻璃及近看可见的下排帘面。上方的棕色封檐托住一道连续的绿色起伏饰带。', 'estimated': '2015年12月的窗扇分格与2021年不同，作品取后者的可见状态。两处街景的交点相距该号地址点约1.9米；店招右缘用于定位。梃距和窗高按全景角度展开，玻璃背后及屋顶深处未获实测。', 'viewer_page': 'pingliang-629-upper-window-band.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
