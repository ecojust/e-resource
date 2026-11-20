"""Rebuild the documented exterior of Fudan's former National Shanghai Medical College."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from campus import model,PALETTE
ID='xuhui-medical-college-east-building-one'
SCOPE='东安路131号东一号楼在修缮前实照中的草坪侧大礼堂、两翼方亭、十一开间黄琉璃瓦歇山顶，以及南坡九个老虎窗和朝明道楼的外凸楼梯间。底部树荫遮挡处、侧墙窗列、构件进深及檐口彩绘按照片概括。'
META={'id':ID,'name':'国立上海医学院东一号楼（草坪立面、歇山顶与两翼方亭）','viewer_page':'medical-college-east-one.html',
      'status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,'reference_height_m':20.60,
      'estimated':'平面以实名东1号楼地块测算，主檐约15.92米、主脊约19.83米，兽吻约20.60米。细部均为影像估计。','interiors_modeled':False,
      'source_register':'source/precise/'+ID+'/reference-review.json',
      'coordinate_convention':'Local X along the main wing towards east-northeast, local Y toward the north lawn, Z up.',
      'copyright':'Original architectural geometry and colours. The cited photos serve as visual sources.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,model)
