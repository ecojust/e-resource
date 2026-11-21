"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from entrance import PALETTE,add_building
META={'id': 'yangpu-tongji-wenyuan-entrance-canopy', 'name': '同济大学文远楼正门雨篷与三柱门廊', 'viewer_page': 'tongji-wenyuan-entrance-canopy.html', 'scope': '雨篷下在2015年和2018年照片都可辨的三根前柱，以及右侧回柱、台阶、两扇入口门及门上亮窗。', 'model_scope_zh': '雨篷下在2015年和2018年照片都可辨的三根前柱，以及右侧回柱、台阶、两扇入口门及门上亮窗。', 'status': 'photo-informed-architectural-component', 'interiors_modeled': False, 'estimated': '按前柱直径0.314米、正面柱距1.85米设比，伸出深度和地面总高为两张照片的近似值。', 'coordinate_convention': 'Metres. X traverses the front row; Y increases towards the entrance, Z points up.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
