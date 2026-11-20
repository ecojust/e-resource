"""Package the original curved elevation of the residence at 250 Duolun Road."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from duolun_geometry import PALETTE,add_building

ID='hongkou-duolun-250'
SCOPE='多伦路250号住宅现存两层弧形街面、中门、摩尔式拱窗、中央阳台及女儿墙。北侧、西侧的临街窗组参照照片；后墙、屋面、纹样和全部尺寸为估计。'
META={'id':ID,'name':'多伦路250号住宅（弧形街面与中门）','status':'original-photo-informed-exterior',
      'viewer_page':'duolun-250.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,
      'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
      'coordinate_convention':'Metre-scale native XYZ with the curved front facing -Y. The verified map placement uses a clockwise 137.18 degree heading; GLB is Y-up.',
      'copyright':'Original geometry MIT. No photographs embedded.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
