"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from iron_gallery import PALETTE,add_building
META={'id': 'xuhui-baoqing-no3-iron-gallery', 'name': '宝庆路20号花园住宅三号楼三跨铁栏廊', 'viewer_page': 'baoqing-no3-iron-gallery.html', 'status': 'photo-informed-architectural-component', 'model_scope_zh': '上海市轻工业研究所三号楼南向二层正中的三跨走廊，含红砖柱、石质栏板及压顶、铸铁路栏和后退窗列。', 'scope': '上海市轻工业研究所三号楼南向二层正中的三跨走廊，含红砖柱、石质栏板及压顶、铸铁路栏和后退窗列。', 'interiors_modeled': False, 'source_register': 'source/precise/xuhui-baoqing-no3-iron-gallery/reference-review.json', 'estimated': '开间、石带和栏杆依照片作透视比例估计，目前现场图片没有可追溯的米尺。上方阁楼和底层前厅另属本栋。', 'coordinate_convention': 'X increases to the right on the south garden front. Y is inward, Z from the bottom of the pale upper-gallery apron.', 'copyright': 'Original architectural geometry and materials under MIT; reference photographs retain their own copyrights.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
