"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from brick_arcade import PALETTE,add_building
META={'id': 'jingan-percy-woo-three-pointed-arches', 'name': '吴培初住宅三联尖券窗与双螺旋石柱', 'scope': '取红砖墙身中段的三道尖券、券下浅色窗头和退入的三樘窗。相邻窗之间保留两根螺旋石柱及柱颈、涡卷和方顶板。', 'model_scope_zh': '取红砖墙身中段的三道尖券、券下浅色窗头和退入的三樘窗。相邻窗之间保留两根螺旋石柱及柱颈、涡卷和方顶板。', 'estimated': '以Fayhoo 2019年1月27日的正面照片为据。取单窗券内宽约1.01米为名义尺度，券高约0.76米；柱身起伏和盲券后退深度按照可见阴影估算。', 'viewer_page': 'percy-woo-three-pointed-arches.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
