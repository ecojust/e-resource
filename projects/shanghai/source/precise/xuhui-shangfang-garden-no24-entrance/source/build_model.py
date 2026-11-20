"""Package the documented service courtyard entrance at Shangfang Garden No. 24."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from entrance import PALETTE, make_entrance

ID = 'xuhui-shangfang-garden-no24-entrance'
SCOPE = '淮海中路1285弄上方花园24号沿北侧支弄的低墙门洞、张元济故居文保铭牌、圆牌、电表柜及门上通风雨棚。'
META = dict(id=ID, name='上方花园24号张元济故居弄门',
            status='original-photo-informed-exterior', scope=SCOPE, model_scope_zh=SCOPE,
            viewer_page='shangfang-garden-no24.html',
            estimated='尺寸、雨棚进深和门轴在已定位24号房屋北立面的具体位置均为估算。',
            coordinate_convention='Local glTF +X follows the frontage westward, +Y is up and +Z faces the northern lane.',
            source_register=f'source/precise/{ID}/reference-review.json', interiors_modeled=False,
            copyright='Original geometry MIT. Inscription outline subset SIL OFL 1.1. Reference photographs are linked.')

if __name__ == '__main__':
    build(SOURCE, META, PALETTE, make_entrance)
