"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from arched_window import PALETTE,add_building
META={'id': 'hongkou-anglo-chinese-school-arched-window', 'name': '英华书馆双色砖券窗与镂花裙板', 'viewer_page': 'anglo-chinese-school-arched-window.html', 'status': 'photo-informed-architectural-component', 'scope': '2011年署名照片中右侧的一孔上层窗，以双色砖券、中央双扇竖栏、两侧横分玻璃及窗下三格五组卷花裙板为界。', 'model_scope_zh': '2011年署名照片中右侧的一孔上层窗，以双色砖券、中央双扇竖栏、两侧横分玻璃及窗下三格五组卷花裙板为界。', 'interiors_modeled': False, 'source_register': 'source/precise/hongkou-anglo-chinese-school-arched-window/reference-review.json', 'estimated': 'Opening width is estimated at 3.12 m. The ratio of the arch rise to opening and of skirt height to width follows the photograph. Absolute width, frame depths, metalwork thickness and unseen section profiles remain approximate.', 'coordinate_convention': 'x across the facade, outward -y, z up from cropped lower stringcourse.', 'copyright': 'Original model and materials under MIT.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
