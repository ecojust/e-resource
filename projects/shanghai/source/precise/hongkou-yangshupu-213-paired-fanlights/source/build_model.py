"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from fanlights import PALETTE,add_building
META={'id': 'hongkou-yangshupu-213-paired-fanlights', 'name': '杨树浦路213号门侧二层双券扇窗', 'viewer_page': 'yangshupu-213-paired-fanlights.html', 'status': 'photo-informed-architectural-component', 'scope': '2018年原照片中，213号门旁灰砖街墙上的两樘二层红砖券窗。窗内三道放射窗梃与下层双扇均可辨。', 'model_scope_zh': '2018年原照片中，213号门旁灰砖街墙上的两樘二层红砖券窗。窗内三道放射窗梃与下层双扇均可辨。', 'interiors_modeled': False, 'source_register': 'source/precise/hongkou-yangshupu-213-paired-fanlights/reference-review.json', 'estimated': '照片可量窗跨宽、窗券起拱、扇窗分格与砖圈比例。绝对尺度和墙厚为估算。', 'coordinate_convention': 'Metres. X follows the facade, -Y faces the street, and Z is measured above the bottom of this upper-storey fragment.', 'copyright': 'Original geometry and materials under MIT.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
