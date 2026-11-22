"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from exchange_bay import PALETTE,add_building
META={'id': 'jingan-yongxing-telephone-exchange-arched-bay', 'name': '上海电话局大楼旧址街角叠券与三联长窗', 'scope': '取永兴路546号街角弧面上的中央单窗与上层三道窄窗。下窗外为同心多层券框，窗顶扇形放射灰缝与两侧平砌灰缝相接；半圆拱上方有一道横向窗槛。', 'model_scope_zh': '取永兴路546号街角弧面上的中央单窗与上层三道窄窗。下窗外为同心多层券框，窗顶扇形放射灰缝与两侧平砌灰缝相接；半圆拱上方有一道横向窗槛。', 'estimated': '据Fayhoo于2019年4月19日拍摄的原上海电话局大楼量取。模型取样宽3.64米，石券进深、弧面曲率及铁窗框厚度由照片比例估计。', 'viewer_page': 'yongxing-telephone-exchange-arched-bay.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
