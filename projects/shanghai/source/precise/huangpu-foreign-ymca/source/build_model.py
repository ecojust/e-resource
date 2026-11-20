"""Build the historical Foreign YMCA street block on West Nanjing Road."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from sports_hall import PALETTE, make_hall

ID = 'huangpu-foreign-ymca'
SCOPE = '南京西路150号体育大厦的临街主楼，含三联高拱、菱纹饰砖、双翼塔楼和退入的上部中庭。后场产权、地下空间及室内泳池不在本次模型范围。'
META = {'id':ID, 'name':'西侨青年会（上海体育大厦临街主楼）', 'status':'original-photo-informed-exterior',
        'scope':SCOPE,'model_scope_zh':SCOPE,'viewer_page':'foreign-ymca.html',
        'estimated':'平面以冻结地图单体为界。楼高、砖材色彩、退台深度、遮挡处开窗和檐口线脚按照片及航片比例估计。',
        'coordinate_convention':'GLB +X points northeast along West Nanjing Road, +Y is up, +Z faces the street to the southeast.',
        'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
        'copyright':'Original geometry MIT. The four-character sign uses a renamed SIL OFL 1.1 typeface subset. No photographic textures.'}

if __name__ == '__main__':
    build(SOURCE,META,PALETTE,make_hall)
