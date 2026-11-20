"""Build the two-court research hall and its east-facing seven-bay portico."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from research_hall import PALETTE,add_hall

ID='xuhui-yueyang-320-research-building'
SCOPE='岳阳路320号在君楼面向岳阳路的东立面、七券入口、两翼与两处开敞内院。屋顶轮廓据徐汇区斜俯照片及三期航照还原。'
META=dict(id=ID,name='岳阳路320号在君楼（七券门廊与双内院）',viewer_page='yueyang-research-building.html',
          scope=SCOPE,model_scope_zh=SCOPE,status='historic-east-facade-and-two-court-envelope',
          estimated='据两份实照、双院建筑足迹、三期航片估计建筑高度、屋顶与开间。西侧和侧院墙以素面表示。',
          coordinate_convention='GLB +Z points toward Yueyang Road, +X runs north-northwest along the east facade, +Y up.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/identity-review.json',
          copyright='Original mesh MIT. Reference images retain their individual rights.')


if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_hall)
