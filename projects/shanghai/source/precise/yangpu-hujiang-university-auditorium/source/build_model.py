"""Build the principal University Auditorium of Hu-chiang University."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))

from package_architectural_model import build
from hall import model
from tracery import PALETTE

ID = 'yangpu-hujiang-university-auditorium'
SCOPE = ('上海理工大学校档所载1937年大学主礼堂，采用修缮后照片可见的红瓦主坡顶、'
         '五联尖券山墙花窗、深门洞、长墙的两枚圆窗与尖券窗列。西南端和受树遮挡的长墙窗数'
         '依据可见段估计。北侧联体思魏堂的独立体量与东侧格致堂保留。')
META = {'id': ID, 'name': '沪江大学大学礼堂（1937年主礼堂）',
        'viewer_page': 'hujiang-university-auditorium.html', 'reference_height_m':20.4,
        'status':'original-photo-informed-exterior','scope':SCOPE,'model_scope_zh':SCOPE,
        'estimated':'地块长约37.20米、端墙宽约17.08米，高度和构件进深由源体和外观照片估算。',
        'interiors_modeled':False,'source_register':'source/precise/'+ID+'/reference-review.json',
        'coordinate_convention':'X northwest across the northeast end gable, Y southwest along the ridge, Z up.',
        'copyright':'Original modeled and coloured geometry, without embedded photographs.'}

if __name__ == '__main__':
    build(SOURCE,META,PALETTE,model)
