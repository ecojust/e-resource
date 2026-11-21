"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from garden_arcade import PALETTE,add_building
META={'id': 'xuhui-anting-villa-garden-arcade', 'name': '安亭别墅1号楼花园券廊', 'viewer_page': 'anting-villa-garden-arcade.html', 'status': 'photo-informed-architectural-component', 'scope': '2013年花园正面照片中三券廊的中央与画面右侧两跨，包括白色层拱、柱头、内退券门、檐口筒瓦、两盏吊灯与对应的瓶栏。', 'model_scope_zh': '2013年花园正面照片中三券廊的中央与画面右侧两跨，包括白色层拱、柱头、内退券门、檐口筒瓦、两盏吊灯与对应的瓶栏。', 'interiors_modeled': False, 'source_register': 'source/precise/xuhui-anting-villa-garden-arcade/reference-review.json', 'estimated': '以原片375×202像素局部放大一倍读线，两个券心相隔约145像素，即原照72.5像素。以原521长边27.16米对约770像素的总立面作粗标，券心距约2.56米。树木遮蔽端角，绝对比例及进深为估计。', 'coordinate_convention': 'X across the arcade, positive Y toward the rear doors, Z vertical.', 'copyright': 'Original geometry and materials under MIT. Photo reference by Legolas1024, Wikimedia Commons, CC BY-SA 4.0. No photographic textures.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
