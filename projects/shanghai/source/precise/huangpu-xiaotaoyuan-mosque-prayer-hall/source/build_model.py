"""Package the photographed two-storey prayer hall, corner domes and rooftop pavilion."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from court_front import PALETTE
from prayer_hall import model

ID='huangpu-xiaotaoyuan-mosque-prayer-hall'
SCOPE=('依2014年远照、2015年和2025年院内实照，以及两期影像重建52号主礼拜楼。'
       '包括东面三门三窗、柱廊与“顯揚正教”匾，四座绿色角穹顶、中央望月亭和月牙冠杆。'
       '高门楼、东侧及南侧房舍、净身堂和附近24号女寺另列。角亭内部、侧后壁细部及高度按可见轮廓估算。')
META={'id':ID,'name':'小桃园清真寺主礼拜殿（院内东立面及五处屋顶构件）',
      'viewer_page':'xiaotaoyuan-prayer-hall.html','model_scope_zh':SCOPE,'scope':SCOPE,
      'reference_height_m':23.34,'status':'original-photo-informed-exterior',
      'estimated':'实名地块包含数栋房舍，带四座角穹顶的主礼拜楼估计长24.9米、宽18.8米，主体和望月亭高度按实照比例估计。',
      'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,
      'coordinate_convention':'X north-northwest along the court-facing east elevation, Y west-southwest into the hall, Z up.',
      'copyright':'Original geometry and colours. Four-character plaque uses an attributed SIL-OFL font subset; photographs are not embedded.'}

if __name__=='__main__':
    build(SOURCE,META,PALETTE,model)
