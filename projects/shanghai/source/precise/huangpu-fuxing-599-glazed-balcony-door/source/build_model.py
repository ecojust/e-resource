"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from balcony_door import PALETTE,add_building
META={'id': 'huangpu-fuxing-599-glazed-balcony-door', 'name': '复兴中路599号住宅二层格窗阳台门与细铁栏', 'scope': '599号院内住宅的二层露台。狭高的暗红色门上半分成两组格窗，下半是四格浅凹门板；门外挑台的铁栏向侧墙折回。', 'model_scope_zh': '599号院内住宅的二层露台。狭高的暗红色门上半分成两组格窗，下半是四格浅凹门板；门外挑台的铁栏向侧墙折回。', 'estimated': '以Antigng在2018年拍摄的原图量门框四角，并校正斜视读格。按门洞约宽1.02米、高2.74米估算，铁栏各根的间距、进深及其他被枝叶挡住的部分为近似。', 'viewer_page': 'fuxing-599-glazed-balcony-door.html', 'interiors_modeled': False, 'coordinate_convention': 'Local X follows the facade, Y points inward and Z is up. Dimensions are estimated, in metres.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
