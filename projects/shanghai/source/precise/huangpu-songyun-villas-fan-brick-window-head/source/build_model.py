"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from fan_brick_window import PALETTE,add_building
META={'id': 'huangpu-songyun-villas-fan-brick-window-head', 'name': '松韵别墅总弄转角扇砖窗楣与木窗上扇', 'scope': '松韵别墅总弄转角楼的二层，木窗上方以红褐色立砖排成扇形，外圈另砌窄券。窗楣以上保留一段齿砖檐口，以下可见一对方形上窗与下扇上部。', 'model_scope_zh': '松韵别墅总弄转角楼的二层，木窗上方以红褐色立砖排成扇形，外圈另砌窄券。窗楣以上保留一段齿砖檐口，以下可见一对方形上窗与下扇上部。', 'estimated': '依据2017年8月Antigng拍摄的《松韵别墅总弄》全幅原照，以窗框四个交点校正透视。暂按窗框宽1.26米、上扇高0.73米换算。穿过下窗的电缆后方和转角另一扇窗均超出本件取样范围。', 'viewer_page': 'songyun-villas-fan-brick-window-head.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
