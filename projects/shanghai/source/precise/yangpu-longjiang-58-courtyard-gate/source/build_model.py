"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from courtyard_gate import PALETTE,add_building
META={'id': 'yangpu-longjiang-58-courtyard-gate', 'name': '龙江路58号住宅院门、门牌与院墙通气孔', 'scope': '沿龙江路两处街景测得58号院门。作品取2015年1月的实景，保留红木门上的信箱和两道横木、右上绿色门牌、三道竖长通气孔及墙帽下的方孔；左侧的铁栏窗与突出的窗台按同一墙面测绘。', 'model_scope_zh': '沿龙江路两处街景测得58号院门。作品取2015年1月的实景，保留红木门上的信箱和两道横木、右上绿色门牌、三道竖长通气孔及墙帽下的方孔；左侧的铁栏窗与突出的窗台按同一墙面测绘。', 'estimated': '58号门牌在2015年正面可读；2021年的同址已有新雨罩和不同颜色的墙脚。三处竖孔的测得宽度约0.12米、高约0.40米。门牌下排小字和门后内部未获清楚记录，墙厚与木门进深为估计。', 'viewer_page': 'longjiang-58-courtyard-gate.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
