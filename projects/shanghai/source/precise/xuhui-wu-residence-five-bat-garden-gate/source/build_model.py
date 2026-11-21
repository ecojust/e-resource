"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from garden_gate import PALETTE,add_building
META={'id': 'xuhui-wu-residence-five-bat-garden-gate', 'name': '吴氏花园住宅庭院五蝠石券仪门', 'viewer_page': 'wu-residence-five-bat-garden-gate.html', 'status': 'photo-informed-architectural-component', 'model_scope_zh': '安福路201号庭院内的单孔仪门，含五蝠内券、正面云纹石券、回纹檐带及绿琉璃瓦脊。', 'scope': '安福路201号庭院内的单孔仪门，含五蝠内券、正面云纹石券、回纹檐带及绿琉璃瓦脊。', 'interiors_modeled': False, 'source_register': 'source/precise/xuhui-wu-residence-five-bat-garden-gate/reference-review.json', 'estimated': '前方树叶遮挡两侧墙缘。净宽用1.22米作比例基准；通道深、脊端与石蝠圆雕的不可见面属于目测近似。', 'coordinate_convention': 'X increases to the right from the ceremonial gate approach. Y increases beneath the arch, Z above its paving.', 'copyright': 'Original architectural geometry and materials under MIT; reference photographs retain their own copyrights.'}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
