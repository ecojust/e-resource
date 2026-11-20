"""Package the photographed, restored Chongsi Building of Xuhui High School."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from school import PALETTE,model
ID='xuhui-chongsi-building'
SCOPE='虹桥路68号崇思楼2009–2010年修缮后的南北主立面、中央入口、分段半圆柱与石饰、石板双折屋面及老虎窗。端墙按斜照近似，校园邻楼、连廊及室内不在模型内。'
META={'id':ID,'name':'徐汇公学崇思楼（修复后南北立面与孟莎屋顶）','viewer_page':'chongsi-building.html',
      'status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'reference_height_m':21.75,'estimated':'施工资料给出轴线66.140×25.144米，南面檐高约14.52米，主脊约21.66米。屋架、柱廊进深及端墙部分为照片估计。','interiors_modeled':False,
      'source_register':'source/precise/'+ID+'/reference-review.json',
      'coordinate_convention':'Local X follows south elevation toward the east, Y north into the footprint, Z up.',
      'copyright':'Original model geometry and colours. Source photos are linked as reference and are not textures.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,model)
