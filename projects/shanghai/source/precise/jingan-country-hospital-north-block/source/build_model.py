"""Build the north block and transverse link from the reviewed architectural module."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from north_block import PALETTE, add_north_block

ID = 'jingan-country-hospital-north-block'
SCOPE = '北翼入口、街侧窗墙、东侧立面与中部连接体的室外外观；北侧立面门廊、窗棂、檐线及可见屋面按资料估计。'
METADATA = {
    'id':ID,'name':'宏恩医院历史主楼北翼与中部门诊连接体',
    'status':'original-photo-informed-exterior','viewer_page':'country-hospital-north.html',
    'scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,
    'coordinate_convention':'Local GLB +X toward photo right (west), +Y up, +Z toward north entrance.',
    'interiors_modeled':False,'source_register':f'source/precise/{ID}/reference-review.json',
    'lettering':{'text':'华东医院','font':'Hospital Plaque Subset Regular','font_license':'SIL OFL 1.1','traced':False},
    'copyright':'Original geometry MIT; original plaque font subset under SIL OFL 1.1. No photo pixels embedded.',
}

if __name__ == '__main__':
    build(SOURCE,METADATA,PALETTE,add_north_block)
