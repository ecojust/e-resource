"""Build the documented central section of former Zhongshan Hospital, Building 3."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from historic_pavilion import PALETTE, add_building

ID='xuhui-zhongshan-hospital-main-building'
SCOPE='医学院路136号中山医院3号楼中央主楼，表现四层病房立面、五层平台、黄琉璃瓦歇山顶及南坡五座老虎窗。东西翼原生体量、独立附楼和现代病区分别保留。尺寸和柱距估计，未复原内饰。'
META={'id':ID,'name':'中山医院3号楼（历史中央主楼）','status':'original-photo-informed-exterior','viewer_page':'zhongshan-hospital-main.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres. +X follows the long roof east-northeast; +Y faces the historic north forecourt.','copyright':'Original geometry MIT. No photographs, third-party models or logos embedded.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
