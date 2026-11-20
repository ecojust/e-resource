"""Build Pure Heart Church's documented northeast re-entrant courtyard."""
from pathlib import Path
import sys

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from courtyard import PALETTE,add_courtyard

ID='huangpu-pure-heart-church'
SCOPE='清心堂主堂东北内庭的两段折角红砖墙、弧顶窗与木窗格、沿外墙的两趟石梯、贯通至平台下的中央门洞及「清心堂」额。'
META=dict(id=ID,name='清心堂主堂东北内庭（两翼拱窗、双梯与中央门洞）',viewer_page='pure-heart-church.html',
          scope=SCOPE,model_scope_zh=SCOPE,status='documented-northeast-courtyard-relief',
          estimated='两翼与底图曲尺形范围相配，局部窗格、弧线、踏步及构件厚度参考地面照片按比例估算。',
          coordinate_convention='GLB +Z faces northeast into the court, +X northwest and +Y up. The two brick walls are perpendicular.',
          interiors_modeled=False,source_register=f'source/precise/{ID}/reference-review.json',
          copyright='Original model MIT. Photographs retain their source rights. Three-glyph font subset SIL OFL 1.1.')
if __name__=='__main__':
    build(SOURCE,META,PALETTE,add_courtyard)
