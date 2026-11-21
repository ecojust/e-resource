"""Build the Sichuan Middle Road facade at 106–110, WGS84 owner 460."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from sichuan_front import PALETTE,make_front

ID='huangpu-asia-realty-sichuan-front'
SCOPE='四川中路106–110号普益大楼临街西立面，五开间三联窗、两端石翼、巨柱、中央小券门和南端大券门。'
META=dict(id=ID,name='普益大楼四川中路街面',status='original-photo-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,viewer_page='asia-realty-building.html',estimated='1921至1922年建造。窗轴、券门、柱间及檐形按2015年1月2日照片表现。材色、楼层高程和建筑截面进深为估计，北端照片外的底层沿用城景原楼。',coordinate_convention='X runs south along the street. Y runs east into the building. glTF +Y is up.',source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,copyright='Original MIT geometry. Photographs are not embedded.')
if __name__=='__main__':build(SOURCE,META,PALETTE,make_front)
