"""Package the independent Yuyuan Road gatehouse of Bubbling Well Lane."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from gate_geometry import PALETTE,gatehouse

ID='jingan-bubbling-well-lane-gate'
SCOPE='愚园路395弄中央三拱门楼的临街砖立面、门洞、两层窗与匾额。通道、侧后墙及屋面按影像估计，铁门扇以收向两侧的位置呈现。两翼住宅和弄内各号单列。'
META={'id':ID,'name':'涌泉坊愚园路中央拱门与门楼','status':'original-photo-informed-exterior','viewer_page':'bubbling-well-lane.html','scope':SCOPE,'estimated':SCOPE,'model_scope_zh':SCOPE,'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local X along the street toward the west-southwest, local Y into the lane toward the southeast, Z up. GLB Y is up.','copyright':'Original geometry and procedural materials MIT. Three outlined Noto Chinese glyphs SIL Open Font License 1.1. No photograph is reproduced in the model.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,gatehouse)
