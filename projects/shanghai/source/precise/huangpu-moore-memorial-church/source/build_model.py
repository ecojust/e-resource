"""Package the original street-facing church, its corner tower and attached wings."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from moore_geometry import PALETTE,add_building

ID='huangpu-moore-memorial-church'
SCOPE='西藏中路316号沐恩堂现存外观，含临街三座退进不同的红砖山墙、中央门廊和花窗、大礼堂、西南高方塔与十字架、两侧附楼。东部附楼沿地图轮廓简化，尺寸与内部院落位置依公开资料估算。'
META={'id':ID,'name':'慕尔堂（沐恩堂礼堂与钟楼）','status':'original-photo-informed-exterior','viewer_page':'moore-memorial-church.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Native XYZ metres. The public street front looks toward native -Y; the measured map heading is 68.2 degrees clockwise. GLB is Y-up.','copyright':'Original geometry MIT. No photographs embedded.'}
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_building)
