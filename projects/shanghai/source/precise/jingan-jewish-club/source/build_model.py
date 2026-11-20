"""Package the photographed garden-facing house of the former Jewish Club."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from garden_house import PALETTE,garden_house
ID='jingan-jewish-club'
SCOPE='南京西路722号原犹太人总会南楼，含庭院中央双柱门廊、两组五拱、楼上花瓶栏杆露台、转折翼部与可辨屋顶。北侧垂直翼、院地、街门和同一保护编号内的702号另列。'
META={'id':ID,'name':'原上海犹太人总会南京西路722号南楼','status':'original-photo-informed-exterior','viewer_page':'jewish-club.html','scope':SCOPE,'estimated':SCOPE,'model_scope_zh':SCOPE,'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local +X toward the east end of the garden front, +Y into the house, +Z up. GLB Y up.','copyright':'Original geometric work and procedural materials MIT; no photographic textures.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,garden_house)
