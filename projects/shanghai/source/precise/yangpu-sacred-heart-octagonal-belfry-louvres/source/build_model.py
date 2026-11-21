"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from belfry import PALETTE,add_building
META={'id': 'yangpu-sacred-heart-octagonal-belfry-louvres', 'name': '圣心教堂八角钟楼三面双层百叶窗', 'viewer_page': 'sacred-heart-belfry-louvres.html', 'status': 'photo-informed-architectural-component', 'scope': '2011年12月3日的杭州路349号外观照片中，八角钟楼正面及两侧相邻各一面。每面建上层券口、下层方口、三面转角细柱与两组百叶。', 'model_scope_zh': '2011年12月3日的杭州路349号外观照片中，八角钟楼正面及两侧相邻各一面。每面建上层券口、下层方口、三面转角细柱与两组百叶。', 'interiors_modeled': False, 'estimated': '正面窗宽暂按0.84米。照片决定上下比例、百叶数量和相邻面角度，槽深为估计。', 'coordinate_convention': 'Metres, X along central tower face, outward -Y, Z above lower cut.', 'copyright': 'Original geometry and materials under MIT.', 'source_register': 'source/precise/yangpu-sacred-heart-octagonal-belfry-louvres/reference-review.json'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
