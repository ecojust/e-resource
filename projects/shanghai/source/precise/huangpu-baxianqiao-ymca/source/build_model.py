"""Build the street wing of the former Chinese YMCA at Baxianqiao."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0, str(PROJECT/'tools'))
from package_architectural_model import build
from street_wing import PALETTE, add_street_wing

ID = 'huangpu-baxianqiao-ymca'
SCOPE = '西藏南路123号原青年会凹字形建筑的西侧临街翼，含双檐、端部和门廊。北部较高后楼、东翼与庭院另待核。'
META = {'id':ID,'name':'八仙桥基督教青年会大楼（西藏南路双檐临街翼）',
        'status':'original-photo-informed-exterior','viewer_page':'baxianqiao-ymca.html',
        'scope':SCOPE,'model_scope_zh':SCOPE,'estimated':'层高、窗格、檐曲线、斗拱和彩枋及简化门雕按照片估计。',
        'coordinate_convention':'Local GLB +X toward SSE along the street, +Y up, +Z toward South Xizang Road.',
        'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
        'copyright':'Original model MIT; three plaque glyphs use an OFL 1.1 subset. No source photos embedded.'}

if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_street_wing)
