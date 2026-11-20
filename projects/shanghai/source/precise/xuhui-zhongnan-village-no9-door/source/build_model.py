"""Package the documented No. 9 door of Zhongnan Village."""
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from door import PALETTE, make_door

ID = 'xuhui-zhongnan-village-no9-door'
SCOPE = '淮海中路1670弄中南新邨9号临支弄木门、几何折线气窗、锁把及绿色9号门牌。'
META = dict(id=ID,name='中南新邨9号木门与气窗',status='original-photo-informed-exterior',
            scope=SCOPE,model_scope_zh=SCOPE,viewer_page='zhongnan-village-no9.html',
            estimated='依据2024年区房管局发表的门牌近照估算尺寸。门扇底部处在照片下沿以外，竖板按同一方向延续。北侧具体门轴位置按分户标点估配。',
            coordinate_convention='Local glTF +X follows the front westward, +Y is up and +Z faces the north-side lane.',
            source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
            copyright='Original geometry MIT. Reference images are linked and are not embedded in the model.')

if __name__ == '__main__':
    build(SOURCE,META,PALETTE,make_door)
