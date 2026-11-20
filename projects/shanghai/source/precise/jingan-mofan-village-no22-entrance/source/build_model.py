"""Build the photo-documented facade bay at No. 22, Mofan Village."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from entrance import PALETTE, make_entrance

ID = 'jingan-mofan-village-no22-entrance'
SCOPE = '延安中路877弄22号面向北侧通道的一层入口，含门槛、凹门廊、椭圆与交叉铁栅、绿色门牌及左侧红色木窗。'
META = dict(id=ID, name='模范邨22号冒广生旧居入口', status='original-photo-informed-exterior',
            scope=SCOPE, model_scope_zh=SCOPE, viewer_page='mofan-village-no22.html',
            estimated='构件尺寸由2021年发表的22号门牌近照估算。1941年名录与街道资料支持门址，北排的具体落点及原有材料颜色仍有误差。',
            coordinate_convention='Local glTF +X follows the facade to the west-southwest, +Y is up and +Z faces out toward the north lane.',
            source_register=f'source/precise/{ID}/reference-review.json', interiors_modeled=False,
            copyright='Original geometry MIT. Research photographs are linked and have not been used as textures.')

if __name__ == '__main__':
    build(SOURCE,META,PALETTE,make_entrance)
