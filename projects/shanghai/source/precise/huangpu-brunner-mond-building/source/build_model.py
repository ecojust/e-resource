"""Build the surviving east street elevation at No. 133 Middle Sichuan Road."""
from pathlib import Path
import hashlib
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build, POSTAL
sys.path.insert(0,str(POSTAL))
from street_elevation import PALETTE, add_geometry

ID='huangpu-brunner-mond-building'
SCOPE=('四川中路133号东向五开间正立面，含底层五券洞、内退中门和踏级、中轴两根槽柱、'
       '通高钢窗、现存科林斯柱头、贝壳卷饰山花、上部两层退台及其屋面前缘。其余侧后墙、屋顶设施和历史已佚雕塑另计。')
META={'id':ID,'name':'卜内门大楼（四川中路五开间东立面）','viewer_page':'brunner-mond.html',
      'status':'original-photo-informed-exterior','model_scope_zh':SCOPE,'scope':SCOPE,'estimated':SCOPE,
      'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
      'coordinate_convention':'Metres. X runs north along the road, Y runs into the building, Z is height.',
      'geometry_helper_sha256':{'source/precise/hongkou-general-post-office/source/postal_geometry.py':
                                hashlib.sha256((POSTAL/'postal_geometry.py').read_bytes()).hexdigest()},
      'copyright':'Original architecture and materials, MIT.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_geometry)
