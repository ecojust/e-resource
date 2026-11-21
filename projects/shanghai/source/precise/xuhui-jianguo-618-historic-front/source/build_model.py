"""Build the independently displayed 2013 photograph study of the 618 Jianguo West Road house."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from balcony_window import PALETTE, make_front

ID='xuhui-jianguo-618-historic-front'
SCOPE='历史住宅一段上层实心栏板挑阳台、板底、两层白色横气窗及墙面分缝。'
META=dict(id=ID,name='建国西路618号住宅挑阳台与窗列',status='historical-photo-informed-facade-study',
          scope=SCOPE,model_scope_zh=SCOPE,viewer_page='jianguo-618-historic-front-history.html',
          estimated='据2013年7月10日的馆方照片制作。几何尺寸、部分受树冠遮挡的分格和颜色为推估。工作名录记住宅建于1948年。',
          coordinate_convention='Standalone photographic elevation detail. glTF +Y points up and +Z faces the viewer.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original MIT geometry. The institutional photograph is cited separately.')
if __name__=='__main__':
    build(SOURCE,META,PALETTE,make_front)
