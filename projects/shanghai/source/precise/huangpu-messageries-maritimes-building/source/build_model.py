"""Build the former Compagnie des Messageries Maritimes office at 9 East Zhongshan No. 2 Road."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from messageries_geometry import PALETTE,make_messageries

ID='huangpu-messageries-maritimes-building'
SCOPE='中山东二路9号法国邮船大楼的临江正面、三层退台轮廓与两侧窗墙。底层深色门楼及金字采用市档案馆外滩馆开放时期的街照。后部受邻楼遮挡的窗列、层高和屋面深度按比例估计。'
META=dict(id=ID,name='法国邮船大楼（浦江大楼）',status='original-photo-informed-exterior',scope=SCOPE,model_scope_zh=SCOPE,
          viewer_page='messageries-maritimes.html',estimated='水刷石外墙、三联窗和门楼比例来自2015年及2021年照片，隐面与屋顶高度没有实测图纸。',
          coordinate_convention='Local GLB +X follows the street toward the northwest, +Y is up and +Z faces the river.',
          source_register=f'source/precise/{ID}/reference-review.json',interiors_modeled=False,
          copyright='Original reconstruction MIT. Original source photos referenced separately. Renamed lettering subset SIL OFL 1.1.')
if __name__=='__main__':
    from final_preview import finish
    build(SOURCE,META,PALETTE,make_messageries)
    finish()
