"""Build the two-storey north book repository and its arcaded eastern walkway."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from library_geometry import PALETTE,make_library

ID='xuhui-zikawei-north-library'
SCOPE='漕溪北路80号徐家汇藏书楼中独立的两层北楼，含六开间庭院长面、东山墙三拱及底层通廊。南侧四层神父楼与库内陈设分列。'
META={'id':ID,'name':'徐家汇藏书楼北楼（原藏书楼）','status':'original-photo-informed-exterior',
      'scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'zikawei-north-library.html',
      'estimated':'按独立具名北楼和三期航片约束外轮廓，窗扇开启情况、瓦片与室内侧墙按实景比例估计。',
      'coordinate_convention':'glTF +X runs east along the south courtyard wall, +Y points up and +Z opens to the courtyard.',
      'source_register':f'source/precise/{ID}/reference-review.json','interiors_modeled':False,
      'copyright':'Original geometry MIT. Independent photographic, cartographic and municipal references are documented separately.'}
if __name__=='__main__':
    from final_preview import finish
    build(SOURCE,META,PALETTE,make_library)
    finish()
