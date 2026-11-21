"""Build the bounded garden elevation documented in the archived institutional photographs."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from garden_front import PALETTE, make_front

ID='xuhui-huaihai-1469-garden-front'
SCOPE='淮海中路1469号1921年花园住宅主屋的中央浅门廊、台阶、两侧横窗与上层腰线局部。'
META=dict(id=ID,name='淮海中路1469号历史花园立面',status='historical-photo-informed-facade-study',
          scope=SCOPE,model_scope_zh=SCOPE,viewer_page='huaihai-1469-garden-front-history.html',
          estimated='比例由馆方两幅档案照片归纳，尺寸、分格与树枝遮挡处的重复装饰均为近似。2010/2011为公开或存档时间，摄影年月未载。',
          coordinate_convention='A standalone elevation study. glTF +Y points up and +Z faces the viewer.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original MIT geometry. Source photographs are referenced separately.')

if __name__=='__main__':
    build(SOURCE,META,PALETTE,make_front)
