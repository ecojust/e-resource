"""Build the measured architectural component as an editable native model and two web meshes."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/"tools"))
from package_architectural_model import build
from broken_pediment import PALETTE,add_building
META={'id': 'jingan-632-no50-broken-pediment', 'name': '延安中路632弄50号住宅西门弧形断山花', 'scope': '取西门柱顶至断山花。两段弧檐在中轴窗前断开，下面的水平檐在柱顶折回、中央内退，弯檐和横檐各有成排小托块。', 'model_scope_zh': '取西门柱顶至断山花。两段弧檐在中轴窗前断开，下面的水平檐在柱顶折回、中央内退，弯檐和横檐各有成排小托块。', 'estimated': '据正门照片量取断口、弧面和柱顶外挑的相对比例。两翼外缘名义间距4.06米，进深及各层线脚厚度为估计。', 'viewer_page': '632-no50-broken-pediment.html', 'source_reference_only': True}
if __name__=="__main__":
    build(SOURCE,META,PALETTE,add_building)
