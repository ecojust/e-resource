"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from arcade import PALETTE,add_building
META={'id': 'hongkou-ohel-moshe-courtyard-brick-arcade', 'name': '摩西会堂庭院首层三连砖券', 'viewer_page': 'ohel-moshe-courtyard-brick-arcade.html', 'status': 'photo-informed-architectural-component', 'scope': '复原长阳路62号庭院立面画面左侧三个首层券洞、四处砖柱及上层走廊下沿的通长线脚。', 'model_scope_zh': '复原长阳路62号庭院立面画面左侧三个首层券洞、四处砖柱及上层走廊下沿的通长线脚。', 'interiors_modeled': False, 'source_register': 'source/precise/hongkou-ohel-moshe-courtyard-brick-arcade/reference-review.json', 'estimated': 'Pier width follows the 2 ft 6 in drawing notation. Bay pitch, arch rise and wall depth are estimated from the exterior photographs.', 'coordinate_convention': 'x along the arcade, outward -y, z above platform.', 'copyright': 'Original geometry and materials under MIT.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
