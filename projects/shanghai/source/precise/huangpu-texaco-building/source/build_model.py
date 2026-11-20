"""Package the curved 2020 street frontage of the former Wheelock and Texaco building."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[3]/'tools'))
from package_architectural_model import build
from street_front import PALETTE,add_front
ID='huangpu-texaco-building'
SCOPE='延安东路110号2020实景所见的弧形街墙、中央两门及双窗、向四川中路延伸的六层窗带和向延安东路延伸的五层街墙。深处建筑与屋内另计。'
META=dict(id=ID,name='德士古大楼（延安东路110号弧形街墙及入口）',viewer_page='texaco-building.html',status='original-photo-and-footprint-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,reference_height_m=22.73,interiors_modeled=False,estimated='源轮廓控制弯度与约72米沿街长度，门窗分格取自实照；街墙高度及进深为按比例估计。',source_register=f'source/precise/{ID}/reference-review.json',coordinate_convention='X follows the chord southwest to northeast, Y toward the interior and Z upward.',copyright='Original geometry and materials MIT. Photographs serve as linked evidence only.')
if __name__=='__main__':build(SOURCE,META,PALETTE,add_front)
