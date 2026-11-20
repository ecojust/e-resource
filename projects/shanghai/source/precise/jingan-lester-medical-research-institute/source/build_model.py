"""Rebuild the documented public exterior of the Lester Institute after the 2024 restoration."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from institute import PALETTE,model
ID='jingan-lester-medical-research-institute'
SCOPE='依据2024年竣工照与启用航拍重建北京西路1320号主楼，包含阶梯形南门塔、贯穿三层的钢窗及黑色窗下墙、玫瑰色花岗石门套、主入口与西侧入口的复原铜灯，以及北部凹口和平屋面。侧背面排列、铜灯细纹、以及屋顶服务体量按可见轮廓估计。'
META={'id':ID,'name':'雷士德医学研究院主楼（2024修缮后外观）','viewer_page':'lester-medical-research.html','status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'reference_height_m':19.744,
      'estimated':'冻结地块长边67.42米。根据2024年修缮后的正面照片估计主楼翼部15.33米、中塔19.74米。','interiors_modeled':False,
      'source_register':'source/precise/'+ID+'/identity-review.json','coordinate_convention':'Local X northeast along the grass elevation, local Y into the building, Z up; origin at the centre of the main front plane.',
      'copyright':'Original modeled and coloured geometry. No photographs are embedded as textures.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,model)
