from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from mint_portico import PALETTE,facade
ID='putuo-central-mint-main-portico'
SCOPE='中央三角山花、六根爱奥尼亚柱、花岗石台阶、左右短窗墙与其阶状冠部。'
META={'id':ID,'name':'中央造币厂主楼三角山花与六柱门廊','viewer_page':'central-mint-main-portico.html','status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'以2016年1月9日具日的主楼照片和早期全景比对；按历史主楼粗面长边估算门廊宽度，柱高、进深、檐口和石色均为照片近似。','source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'X follows the visible main elevation to photo right; Y is inward and Z is height in metres.','copyright':'Original geometry/materials, MIT; no photographic textures. Sign typeface subset uses SIL OFL 1.1.'}
if __name__=='__main__':build(HERE,META,PALETTE,facade)
