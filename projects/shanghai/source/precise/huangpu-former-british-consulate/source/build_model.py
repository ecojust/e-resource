"""Build the former office building, including the original attached court frontage."""
from pathlib import Path
import sys
SRC=Path(__file__).resolve().parent
sys.path.insert(0,str(SRC.parents[3]/'tools'))
from package_architectural_model import build
from office import PALETTE,office
ID='huangpu-former-british-consulate'
SCOPE='中山东一路33号原英国驻沪领事馆办公主楼及照片所见相连法院外墙，参照1911、1913年各立面档案、1929年远照、2011年修缮后花园面与屋顶航片。北侧1882年独立住宅、连接廊、园区其余建筑另列。'
META={'id':ID,'name':'原英国驻沪领事馆办公主楼','status':'original-photo-informed-exterior','viewer_page':'former-british-consulate.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'各层高、材料、檐线与廊深由照片估计，平面按现存屋顶配准。','interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local +X ENE, +Y NNW into the former office building; local +Z up.','copyright':'Original geometry and materials, MIT. Reference photographs are not included.'}
if __name__=='__main__':build(SRC,META,PALETTE,office)
