"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from window_bands import PALETTE,add_building
META={'id': 'xuhui-cavendish-court-street-window-bands', 'name': '凯文公寓北楼沿街红砖带与钢窗', 'viewer_page': 'cavendish-court-street-window-bands.html', 'status': 'photo-informed-architectural-component', 'model_scope_zh': '衡山路525号北楼沿街咖啡店檐上连续两层，取一扇双分格窗、一扇三分格窗、相间的暗红砖带和左侧落水管。', 'scope': '衡山路525号北楼沿街咖啡店檐上连续两层，取一扇双分格窗、一扇三分格窗、相间的暗红砖带和左侧落水管。', 'interiors_modeled': False, 'source_register': 'source/precise/xuhui-cavendish-court-street-window-bands/reference-review.json', 'estimated': '窗宽0.94米和1.92米，窗高1.64米，两层窗台差3.15米。玻璃后退量、砖深和落水管直径按照片估计。', 'coordinate_convention': 'X runs from the downpipe along the frontage, Y is inward and Z begins 0.20 m below the lower sill.', 'copyright': 'Original geometry and materials under MIT. Reference photographs retain their respective copyrights.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
