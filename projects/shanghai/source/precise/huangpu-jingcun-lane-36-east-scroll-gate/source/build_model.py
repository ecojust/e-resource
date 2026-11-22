"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from lane_gate import PALETTE,add_building
META={'id': 'huangpu-jingcun-lane-36-east-scroll-gate', 'name': '静村绍兴路36弄弄口东侧透花铁门', 'scope': '以街面右手完整可见的一扇铁门为范围，黑色框架围住上下两排长条透花和金色圈饰，上缘有七枚矛尖。', 'model_scope_zh': '以街面右手完整可见的一扇铁门为范围，黑色框架围住上下两排长条透花和金色圈饰，上缘有七枚矛尖。', 'estimated': '2020年2月两处街景相机的对应主梃间距约0.78至0.83米，估计完整门扇宽约1.6米。2013年10月影像已可见这种门框与透花。铁门的安装年代及花饰背面尚无实测。', 'viewer_page': 'jingcun-lane-36-east-scroll-gate.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
