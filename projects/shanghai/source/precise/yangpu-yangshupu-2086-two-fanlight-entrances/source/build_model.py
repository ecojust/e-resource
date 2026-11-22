"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from twin_entrances import PALETTE,add_building
META={'id': 'yangpu-yangshupu-2086-two-fanlight-entrances', 'name': '日商上海纺织株式会社旧址街面双券门与扇形亮窗', 'scope': '杨树浦路2086号建筑群临街相邻的两个券门。每樘双扇木门上半部各有九格，券内的两道同心铁条与斜辐条围成扇面，右门外有两柱承挑石过梁。', 'model_scope_zh': '杨树浦路2086号建筑群临街相邻的两个券门。每樘双扇木门上半部各有九格，券内的两道同心铁条与斜辐条围成扇面，右门外有两柱承挑石过梁。', 'estimated': '采用2019年可见的门扇和石框。2015年同一处仍围挡施工，已能辨认两道券与错开的檐口。左门垫高一级、右门接近街面。正面取每扇约0.87至0.94米，进深及灰色填实玻璃均为推定。', 'viewer_page': 'yangshupu-2086-two-fanlight-entrances.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
