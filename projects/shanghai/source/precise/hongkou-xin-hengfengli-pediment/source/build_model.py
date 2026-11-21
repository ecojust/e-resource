"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from pediment import PALETTE,add_building
META={'id': 'hongkou-xin-hengfengli-pediment', 'name': '新恒丰里山阴路85弄门楼题额与盾饰山花', 'viewer_page': 'xin-hengfengli-pediment.html', 'status': 'photo-informed-architectural-component', 'scope': '以2015年山阴路85弄入口的横额、三角山花和盾饰卷叶为界。', 'model_scope_zh': '以2015年山阴路85弄入口的横额、三角山花和盾饰卷叶为界。', 'interiors_modeled': False, 'source_register': 'source/precise/hongkou-xin-hengfengli-pediment/reference-review.json', 'estimated': 'Scale is estimated from the entrance lintel. Letter and carving depths are approximate.', 'coordinate_convention': 'x across the beam, outward -y, z upward from beam soffit.', 'copyright': 'Original model and materials under MIT.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
