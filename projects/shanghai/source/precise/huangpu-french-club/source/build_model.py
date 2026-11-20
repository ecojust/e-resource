"""Package the garden-facing French Club at 58 Maoming South Road."""
from pathlib import Path
import sys
SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from french_geometry import PALETTE,add_building
ID='huangpu-french-club'
SCOPE='茂名南路58号法国总会现存低层会所，含花园南面五窗弧突、两翼各五开间的上层柱廊、端部大拱窗、现存玻璃雨篷和东部宴会厅外轮廓。上部酒店塔另有独立底图。背墙、设备和屋面尺度依据照片与平面估计。'
META={'id':ID,'name':'法国总会（花园饭店历史会所）','status':'original-photo-informed-exterior','viewer_page':'french-club.html','scope':SCOPE,'model_scope_zh':SCOPE,'estimated':SCOPE,'source_register':'source/precise/'+ID+'/reference-review.json','interiors_modeled':False,'coordinate_convention':'Metres in local XYZ, -Y faces the garden. Map heading -13.1 degrees clockwise. Exported glTF is Y-up.','copyright':'Original geometry MIT. No photographs embedded.'}
if __name__=='__main__':build(SOURCE,META,PALETTE,add_building)
