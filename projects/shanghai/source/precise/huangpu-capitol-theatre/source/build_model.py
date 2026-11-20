"""Build the Capitol Building including the historic theatre entrance and two rooftop towers."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from capitol_geometry import PALETTE,make_capitol

ID='huangpu-capitol-theatre'
SCOPE='虎丘路142–146号光陆大楼旧楼临街外壳，含河畔扇形弧面、原戏院街角入口、两座不等高的塔楼。楼内影院、背后现代退台和广学大楼分列。'
META={'id':ID,'name':'光陆大戏院（光陆大楼）','status':'original-photo-informed-exterior',
      'scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'capitol-theatre.html',
      'estimated':'按具名建筑和冻结地块约束主楼；楼层口径有差异，窗列、材质和两座塔的绝对高度按历史与2019、2025实拍估计。',
      'coordinate_convention':'glTF +X follows Huqiu Road approximately south, +Y points up, +Z faces the western street.',
      'source_register':f'source/precise/{ID}/reference-review.json','interiors_modeled':False,
      'copyright':'Original geometry MIT. Reference photographs and the 1927 design plate are documented without embedding their material.'}
if __name__=='__main__':
    from final_preview import finish
    build(SOURCE,META,PALETTE,make_capitol)
    finish()
