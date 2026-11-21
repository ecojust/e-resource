"""Build the attributed Donghu Road street-wall fragment."""
from pathlib import Path
import sys

source=Path(__file__).resolve().parent
project=next(root for root in source.parents if (root/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(project/'tools'))
from package_architectural_model import build
from numbered_wall import PALETTE,add_building,TOP

ID='xuhui-donghu-road-17-numbered-wall'
META=dict(id=ID,name='东湖路17号花园住宅门牌与临街围墙',viewer_page='donghu-road-17-numbered-wall.html',
          status='photo-informed-exterior-study',reference_height_m=TOP,
          scope='东湖路17号公共街面可见的绿色门牌、下方赭红分缝面、上部灰色叠石墙帽与右侧一小段折墙。',
          model_scope_zh='2026年10月拍摄的17号门牌墙段。保留街区原有房屋，门后两栋的历史用途分别待考。',
          estimated='按图中号牌四角校正正面比例。号牌假定宽0.32米、高0.22米；绝对尺寸、短折边角与剖切深度为约值。',
          source_register='source/precise/'+ID+'/reference-review.json',
          coordinate_convention='Metres. Front face runs along +X from the left edge of the photographed wall towards the right bend. Z=0 is the lower cut of this exhibit.',
          interiors_modeled=False,copyright='Original geometry and materials. Numerals are polygonal outlines. Street-name lettering uses an OFL-licensed Noto subset. No photographs are embedded.')
if __name__=='__main__':
    build(source,META,PALETTE,add_building)
