"""Package the two-storey house at 2310 Hongqiao Road."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from villa_geometry import PALETTE,add_villa

ID='changning-luobiegen-garden-villa'
SCOPE='虹桥路2310号罗别根花园英式乡村主宅，两层南花园面、双山墙、中央阳台、东侧窗室与红瓦屋顶；侧后墙、遮挡处与高度含估计。西部狭长连接段、邻排、花园及室内单列。'
META={'id':ID,'name':'罗别根花园主宅（南向双山墙与露木构阳台）','status':'original-photo-informed-exterior','viewer_page':'luobiegen-garden.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json','coordinate_convention':'Local X follows the garden frontage east at 80 degrees, Y heads into the house at 350 degrees, Z up. glTF Y is up.','copyright':'Original geometry and procedural materials MIT. No photographs embedded.'}

if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_villa)
