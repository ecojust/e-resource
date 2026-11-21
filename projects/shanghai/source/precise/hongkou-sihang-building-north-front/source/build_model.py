"""Build the northern street frontage of the Four Banks Building in Hongkou."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from north_front import PALETTE,make_front
ID='hongkou-sihang-building-north-front'
SCOPE='虹口四川北路1274–1290号四行大楼的临街北段，浅色竖墩、六列住宅窗及独立挑檐、顶层弧形阳台和后来店铺的三扇放射形气窗。'
META=dict(id=ID,name='四川北路四行大楼临街北段',status='original-photo-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,
          viewer_page='sihang-building.html',estimated='1932年竣工。2012年照片、2021年四川北路四站街景及市图共同定位。窗扇、材料、门面、檐口、切段深度与层高按影像估计；红砖南段、盛邦国际大厦和内部不在重建范围。',
          coordinate_convention='X runs south along the west elevation. Y points east into the building. glTF +Y is up.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,copyright='Original MIT geometry. Photographs are not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,make_front)
